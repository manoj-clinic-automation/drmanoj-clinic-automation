#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s440.py -- builds the patched live files of kit S440_SCAN_FLOW from the LIVE bytes by anchored edits. Every anchor must occur
exactly once and every source must be at its FROM pin, or the build stops with nothing written.

  porders.py          "Scan ka kaam": the block porders_block_s440.py appended (the five groups, the three answers a person can give,
                      the read door /finance/porders/api/scan-status, the double entries of Marg); the intake link carries ?from=;
                      state() carries 'kaam'; the summary carries the counts; Needs you gains the owner's amount lines.
  porders.html        the ← BACK bar and the up-arrow; section 3 is "Scan ka kaam" with a tap per line.
  purchase_app.py     the matcher keeps what a person decided (purchase_block_s440.py inserted; the pass reads, applies and re-writes the
                      decisions; a CONFIRMED link stays; a refused bill is never offered again); the owner's Scan links page carries
                      the BACK bar, the five groups read-only and the up-arrow.
  asset_register.py   PARENT'S, declared: asset_block_s440.py inserted; the BACK bar and the up-arrow in the base layout; the intake
                      camera-first; the Save card on the slip; the Purchases list / a bill / its scan / a thumbnail / "Galat lane" open,
                      narrowed, to a scanning login.

Usage: make_s440.py --finance /root/finance --assetapp /root/assetapp --out DIR
"""
import argparse
import hashlib
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FROM = {
    "porders.py": "64465af0835bdc5583ae7468cacc8c16",
    "porders.html": "124c4d41b9491203899f324b8a194763",
    "purchase_app.py": "ebe38c681f323782f0a211d1d0879b24",
    "asset_register.py": "1f80773b85583d0f9e3344b74b313389",
}


def md5(b):
    return hashlib.md5(b).hexdigest()


def load(path, name):
    raw = open(path, "rb").read()
    if md5(raw) != FROM[name]:
        sys.exit("REFUSED: %s is %s, not its FROM pin %s" % (path, md5(raw), FROM[name]))
    return raw.decode("utf-8")


def sub(text, old, new, what):
    n = text.count(old)
    if n != 1:
        sys.exit("REFUSED: anchor for '%s' occurs %d times, not once" % (what, n))
    return text.replace(old, new)


def span(text, first, last, new, what):
    """Replace everything from the anchor `first` to the anchor `last` (both included, each exactly once, in that order)."""
    for a in (first, last):
        if text.count(a) != 1:
            sys.exit("REFUSED: span anchor for '%s' occurs %d times, not once" % (what, text.count(a)))
    i, j = text.index(first), text.index(last)
    if j < i:
        sys.exit("REFUSED: span anchors for '%s' are out of order" % what)
    return text[:i] + new + text[j + len(last):]


def block(name, starts):
    b = io.open(os.path.join(HERE, name), "r", encoding="utf-8", newline="").read()
    if "\r" in b or not b.lstrip("\n").startswith(starts) or not b.endswith("\n"):
        sys.exit("REFUSED: %s is not the kit's block" % name)
    return b


# ----------------------------------------------------------------------------- porders.py
def patch_porders(s):
    s = sub(s, "#  Every figure stays as it was; the words are added beside it.\n",
            "#  Every figure stays as it was; the words are added beside it.\n"
            "#\n"
            "#  S440 (D640, F-662, 30-Sep-2026): section 3 is \"Scan ka kaam\" -- ONE list, a tap per line: Scan karo / Yahi bill hai? / Supplier chuno /\n"
            "#  Amount milao / Marg ka intezaar (the block at the foot of this file). state() carries 'kaam'; 'scans' stays as S403 built it\n"
            "#  (unscanned_bills() is unchanged: the month-end checklist still counts every bill with no link).\n", "header")
    s = sub(s, '    return "/scanapp/intake?" + urlencode(q)\n',
            '    q["from"] = "/finance/porders"                           # S440: the intake\'s BACK and its Save card return here\n'
            '    return "/scanapp/intake?" + urlencode(q)\n', "_intake_url: from")
    s = sub(s, "                scans=dict(n=len(bills) + len(rec), bills=bills, received=rec, red=sum(1 for b in bills if b[\"red\"]) + sum(1 for r in rec if r[\"red\"])),\n",
            "                scans=dict(n=len(bills) + len(rec), bills=bills, received=rec, red=sum(1 for b in bills if b[\"red\"]) + sum(1 for r in rec if r[\"red\"])),\n"
            "                kaam=_s440_kaam(con),                                  # S440 (D640): Scan ka kaam -- the five groups\n", "state: kaam")
    s = sub(s, '            out.append(dict(cls="info", target="porders", text="Buying rules for medicines await your approval"))\n',
            '            out.append(dict(cls="info", target="porders", text="Buying rules for medicines await your approval"))\n'
            '        out.extend(_s440_owner_lines(con))                        # S440 (D640): a paper amount reception could not settle\n', "needs_you: owner lines")
    s = sub(s, "    return jsonify(**shortage_summary(con))\n",
            "    sm = shortage_summary(con)\n"
            "    try:                                                      # S440: the counts of Scan ka kaam beside the shortage count (fail-soft)\n"
            "        k = scan_work(con)\n"
            "        sm[\"scan_kaam\"] = dict(n=k[\"n\"], **k[\"counts\"])\n"
            "    except Exception:                                         # noqa: BLE001\n"
            "        pass\n"
            "    return jsonify(**sm)\n", "api_summary: scan_kaam")
    tail = "    return jsonify(ok=True, already=False, approved=rec)\n"
    if not s.endswith(tail) or s.count(tail) != 1:
        sys.exit("REFUSED: porders.py does not end where the S440 block is appended")
    return s + block("porders_block_s440.py", "# ====")


# ----------------------------------------------------------------------------- porders.html
HTML_CSS = (
    " #s440bar{position:sticky;top:0;z-index:30;display:flex;align-items:center;gap:10px;background:#1f3864;color:#fff;margin:-10px -12px 8px;padding:6px 10px}\n"
    " #s440back{display:flex;align-items:center;justify-content:center;min-height:44px;flex:1 1 auto;max-width:60%;background:#fff;color:#1f3864;border-radius:9px;"
    "font-size:18px;font-weight:800;text-decoration:none}\n"
    " #ttl{margin-left:auto;font-weight:600;font-size:15px;text-align:right}\n"
    " #s440up{position:fixed;right:14px;bottom:18px;width:48px;height:48px;border-radius:24px;border:0;background:#1f3864;color:#fff;font-size:24px;display:none;z-index:40}\n"
    " details.kg{border-top:1px solid #e4e0da;margin:0 -14px;padding:0 14px}details.kg>summary{cursor:pointer;padding:10px 0;font-weight:700;font-size:16px}\n"
    " details.kg>summary .n{display:inline-block;min-width:24px;text-align:center;padding:1px 8px;border-radius:12px;background:#fbe7e5;color:#b3261e;font-size:13px}\n"
    " details.kg.calm>summary .n{background:#eee;color:#555}\n"
    " .kline{display:flex;gap:10px;border-top:1px solid #eee;padding:10px 0}.kb{flex:1 1 auto;min-width:0}\n"
    " a.kth{flex:0 0 62px}a.kth img{width:62px;height:82px;object-fit:cover;border:1px solid #ccc;border-radius:6px;background:#eee}a.kth.nopic{display:none}\n"
    " details.kl{margin-top:4px}details.kl>summary{color:#888;font-size:13px;cursor:pointer}details.kl select{font-size:15px;padding:6px}\n"
    " select.kv{font-size:16px;padding:8px;max-width:100%;margin:6px 0}\n"
)

HTML_SEC3 = r'''
 // 3 -- Scan ka kaam (S440, D640): five kinds of line, each with its own buttons and nothing else
 const K=s.kaam||{n:0,counts:{},scan:[],confirm:[],vendor:[],amount:[],wait:[],received:[],suppliers:[]};
 let b=kmsgHtml();
 const pic=x=>'<a class="kth" href="'+esc(x.pdf)+'" target="_blank"><img loading="lazy" src="'+esc(x.thumb)+'" alt="scan" onerror="this.parentNode.className=\'kth nopic\'"></a>';
 const old=x=>x.age?(' · <span class="'+(x.age>3?'red':'muted')+'">'+L("days",x.age)+'</span>'):'';
 const lane=x=>canWrite()?'<details class="kl"><summary>'+L("lane")+'</summary><form method="post" action="/scanapp/bills/'+x.scan+'/lane"><input type="hidden" name="back" value="'+esc(location.pathname+location.search)+'"><select name="lane"><option value="clinic">Clinic bill</option><option value="lab_purchase">Lab purchase</option><option value="other_doc">Other document</option></select> <button class="btn sm">'+L("move")+'</button></form></details>':'';
 const read=x=>'<div class="muted">Scan '+esc(x.stamp)+': '+esc(x.scan_vendor||"—")+' · '+esc(x.scan_no||"—")+' · '+esc(x.scan_amount)+old(x)+'</div>';
 const grp=(id,title,n,inner,open,calm)=>n?('<details class="kg'+(calm?' calm':'')+'" id="kg'+id+'"'+(open?' open':'')+'><summary>'+title+' <span class="n">'+n+'</span></summary>'+inner+'</details>'):'';
 if(!K.n&&!(K.wait||[]).length) b+='<div class="muted">'+L("none3")+'</div>';
 let g1="";
 (K.scan||[]).forEach(x=>{
  g1+='<div class="line"><div class="nm">'+esc(x.vendor)+'</div><div class="muted">bill '+esc(x.bill_no)+' · '+esc(x.date_text)+' · '+esc(x.amount)+old(x)+'</div>'+
      (x.double?'<div class="sent">'+L("double")+' ('+esc((x.double_nos||[]).join(" / "))+')</div>':'')+
      '<a class="btn ok sm" href="'+esc(x.intake)+'">📷 '+L("scan")+'</a></div>';
 });
 (K.received||[]).forEach(x=>{
  g1+='<div class="line"><div class="nm">'+esc(x.vendor)+'</div><div class="muted">'+L("recvd",esc(x.received_text))+(x.red?' · <span class="red">'+L("red",x.age)+'</span>':'')+'</div>'+
      '<a class="btn ok sm" href="'+esc(x.intake)+'">📷 '+L("scan")+'</a></div>';
 });
 b+=grp(1,L("k1"),(K.scan||[]).length+(K.received||[]).length,g1,true);
 let g2="";
 (K.confirm||[]).forEach(x=>{
  g2+='<div class="kline">'+pic(x)+'<div class="kb"><div class="nm">'+esc(x.vendor)+' · bill '+esc(x.bill_no)+'</div><div class="muted">Marg: '+esc(x.date_text)+' · '+esc(x.amount)+'</div>'+read(x)+
      (x.taken_by?'<div class="sent">'+L("taken",esc(x.taken_stamp||("#"+x.taken_by)))+'</div>':'')+
      (canWrite()?'<div><span class="btn ok sm" onclick="kConfirm('+x.scan+','+x.bill_id+',true)">'+L(x.taken_by?"yes2":"yes")+'</span><span class="btn bad sm" onclick="kConfirm('+x.scan+','+x.bill_id+',false)">'+L("no")+'</span></div>':'')+lane(x)+'</div></div>';
 });
 b+=grp(2,L("k2"),(K.confirm||[]).length,g2,true);
 let g3="";
 (K.vendor||[]).forEach(x=>{
  g3+='<div class="kline">'+pic(x)+'<div class="kb">'+read(x)+
      (canWrite()?'<div><select class="kv" id="kv'+x.scan+'"><option value="">'+L("pick")+'</option>'+(K.suppliers||[]).map(v=>'<option>'+esc(v)+'</option>').join("")+'<option value="-">'+L("notlisted")+'</option></select></div><span class="btn ok sm" onclick="kVendor('+x.scan+')">'+L("isvendor")+'</span>':'')+lane(x)+'</div></div>';
 });
 b+=grp(3,L("k3"),(K.vendor||[]).length,g3,true);
 let g4="";
 (K.amount||[]).forEach(x=>{
  g4+='<div class="kline">'+pic(x)+'<div class="kb"><div class="nm">'+esc(x.vendor)+' · bill '+esc(x.bill_no)+'</div><div>Scan <b>'+esc(x.scan_amount)+'</b> · Marg <b>'+esc(x.amount)+'</b></div>'+
      (canWrite()?'<div>'+L("paper")+' <input class="q" style="width:110px" inputmode="decimal" id="ka'+x.scan+'"> <span class="btn ok sm" onclick="kAmount('+x.scan+')">'+L("match")+'</span></div>':'')+lane(x)+'</div></div>';
 });
 b+=grp(4,L("k4"),(K.amount||[]).length,g4,true);
 let g5="";
 (K.wait||[]).forEach(x=>{
  g5+='<div class="kline">'+pic(x)+'<div class="kb">'+read(x)+'<div class="muted">'+esc(EN?(x.note_en||x.note):x.note)+'</div>'+lane(x)+'</div></div>';
 });
 b+=grp(5,L("k5"),(K.wait||[]).length,g5,false,true);
 h+=sec(3,L("s3",K.n),K.n,K.n?'red':'ok',b);
'''

HTML_FUNCS = r'''// S440 (D640): Scan ka kaam -- the three answers a person can give; the line goes when the server has taken it
let KMSG=null;
function kmsgHtml(){if(!KMSG)return "";return '<div class="saved '+(KMSG.kind||"")+'" id="kmsg"><div class="l">'+esc(KMSG.text)+'</div></div>';}
async function kDo(url,body){
 if(BUSY)return;BUSY=true;OPEN[3]=true;
 try{const j=await post(url,body);KMSG={kind:"",text:"✓ "+(j.message||"")};await load();}
 catch(e){KMSG={kind:"err",text:e.message};render();}
 BUSY=false;
}
function kConfirm(scan,bill,yes){kDo("/finance/porders/api/scan/confirm",{scan,bill,yes});}
function kVendor(scan){const v=(el("kv"+scan)||{}).value;if(!v){KMSG={kind:"err",text:L("pickfirst")};render();return;}kDo("/finance/porders/api/scan/vendor",{scan,vendor:v});}
function kAmount(scan){const v=((el("ka"+scan)||{}).value||"").trim();if(!/^\d+(\.\d{1,2})?$/.test(v)){KMSG={kind:"err",text:L("digits")};render();return;}kDo("/finance/porders/api/scan/amount",{scan,paper:v});}
(function(){ // the BACK bar returns to the page the person came from (?from=, a path inside this site), else the portal's tile hub; the up-arrow after a screen
 const f=new URLSearchParams(location.search).get("from");
 if(f&&f.charAt(0)==="/"&&f.charAt(1)!=="/"&&!/[\\"'<>\r\n]/.test(f)) el("s440back").href=f;
 window.addEventListener("scroll",function(){el("s440up").style.display=(window.pageYOffset>window.innerHeight)?"block":"none";});
})();
load();
</script>
'''


def patch_porders_html(s):
    s = sub(s, "<title>Purchase orders</title>\n",
            "<title>Purchase orders</title>\n"
            "<!-- S440_SCAN_FLOW (30-Sep-2026, D640, F-662): section 3 is \"Scan ka kaam\" -- ONE list, a tap per line (Scan karo · Yahi bill hai? · Supplier chuno ·\n"
            "     Amount milao · Marg ka intezaar), each scan with its thumbnail; a sticky BACK bar (to ?from=, else the portal's tile hub) and a floating\n"
            "     up-arrow. Everything the lines show comes from /finance/porders/api/state (kaam); nothing is decided here. -->\n", "html: comment")
    s = sub(s, " table{border-collapse:collapse;width:100%;font-size:14px}td,th{padding:5px 6px;border-bottom:1px solid #eee;text-align:left}td.n{text-align:right}\n</style>\n",
            " table{border-collapse:collapse;width:100%;font-size:14px}td,th{padding:5px 6px;border-bottom:1px solid #eee;text-align:left}td.n{text-align:right}\n"
            + HTML_CSS + "</style>\n", "html: css")
    s = sub(s, '<body>\n<h1 id="ttl">Purchase orders</h1>\n',
            '<body>\n<div id="s440bar"><a id="s440back" href="/portal">← BACK</a><span id="ttl">Purchase orders</span></div>\n'
            '<button id="s440up" aria-label="upar" onclick="window.scrollTo({top:0,behavior:\'smooth\'})">↑</button>\n', "html: the bar")
    s = sub(s, ' s3:["Bill scan karo (%d)","Bill scans pending (%d)"], s4:',
            ' s3:["Scan ka kaam (%d)","Scan work (%d)"],\n'
            ' k1:["Scan karo","To scan"], k2:["Yahi bill hai?","Is this the bill?"], k3:["Supplier chuno","Choose the supplier"], k4:["Amount milao","Match the amount"], k5:["Marg ka intezaar","Waiting for Marg"],\n'
            ' yes:["Haan, yahi hai","Yes, this one"], yes2:["Haan, doosri baar scan hua","Yes, scanned twice"], no:["Nahi","No"], taken:["Is bill ka scan pehle se hai (%s) — yeh wahi kaagaz hai?","This bill already has a scan (%s) — the same paper?"],\n'
            ' pick:["— supplier chuno —","— choose the supplier —"], notlisted:["List mein nahi hai","Not on the list"], isvendor:["Yeh supplier hai","This is the supplier"], pickfirst:["Pehle supplier chuniye.","Choose a supplier first."],\n'
            ' paper:["Kaagaz par amount:","Amount on the paper:"], match:["Milao","Match"], digits:["Sirf ank likhiye — jaise 14442","Digits only — e.g. 14442"],\n'
            ' lane:["Galat lane","Wrong lane"], move:["Hatao","Move"], days:["%d din se","%d days"], double:["Marg mein do baar — Amir ko batao","Entered twice in Marg — tell Amir"],\n'
            ' s4:', "html: the words")
    s = sub(s, ' none3:["Sab bill scan ho gaye.","Every bill is scanned."],', ' none3:["Scan ka koi kaam baaki nahi.","No scan work is waiting."],', "html: none3")
    s = span(s, " // 3 -- bill scans\n", " h+=sec(3,L(\"s3\",s.scans.n),s.scans.n,s.scans.red?'red':(s.scans.n?'':'ok'),b);\n", HTML_SEC3.lstrip("\n"), "html: section 3")
    s = sub(s, " S.ortho.lines.forEach(l=>{if(QTY[l.item]==null)QTY[l.item]=l.short; if(PICK[l.item]==null)PICK[l.item]=l.item;});\n",
            " S.ortho.lines.forEach(l=>{if(QTY[l.item]==null)QTY[l.item]=l.short; if(PICK[l.item]==null)PICK[l.item]=l.item;});\n"
            " if(OPEN[3]==null&&S.kaam&&S.kaam.n)OPEN[3]=true;   // S440: work waiting -- the list is open\n", "html: open section 3")
    s = sub(s, "load();\n</script>\n", HTML_FUNCS, "html: the functions")
    return s


# ----------------------------------------------------------------------------- purchase_app.py
def patch_purchase_app(s):
    s = sub(s, "def _ensure_s439(con):\n", block("purchase_block_s440.py", "# ----") + "def _ensure_s439(con):\n", "the S440 functions")
    s = sub(s, "        who           TEXT,                       -- 'S439 learned from scan <id>'\n        at            TEXT)\"\"\")\n",
            "        who           TEXT,                       -- 'S439 learned from scan <id>'\n        at            TEXT)\"\"\")\n"
            "    have = {r[1] for r in con.execute(\"PRAGMA table_info(purchase_scan_state)\")}      # S440 (D640): what a person decided -- additive columns\n"
            "    for col, typ in S440_STATE_COLS:\n"
            "        if col not in have:\n"
            "            con.execute(\"ALTER TABLE purchase_scan_state ADD COLUMN %s %s\" % (col, typ))\n", "_ensure_s439: the decision columns")
    s = sub(s, '    """One scan against one Marg bill -> (rank, grade, rule) or None. The six rules are in the header above."""\n',
            '    """One scan against one Marg bill -> (rank, grade, rule) or None. The six rules are in the header above."""\n'
            '    if b["id"] in s.get("_no", ()):                           # S440: a person said this scan is NOT this bill\n'
            '        return None\n', "_match_s439: refused bills")
    s = sub(s, '    tails, amt = s["_tails"], s["amount_p"]\n    canon, how, _sc = s["_vendor"]\n',
            '    tails, amt = s["_tails"], s["amount_p"]\n    canon, how, _sc = s["_vendor"]\n'
            '    no = s.get("_no", ())                                     # S440: bills a person refused for this scan are never named again\n'
            '    s["_likely"] = None                                       # S440: the bill the sentence names, also when it already has a scan\n', "_why_s439: no / likely")
    s = sub(s, '        same = [b for b in bills if tails and b["_tails"] and b["_tails"][0] in tails and gap(b) <= S439_HINT_DAYS]\n        if same:\n            b = min(same, key=near)\n',
            '        same = [b for b in bills if tails and b["_tails"] and b["_tails"][0] in tails and gap(b) <= S439_HINT_DAYS and b["id"] not in no]\n        if same:\n            b = min(same, key=near)\n'
            '            s["_likely"] = b["id"]\n', "_why_s439: same tail")
    s = sub(s, '        close = [b for b in bills if b["_skey"] == canon and likely(b) and gap(b) <= S439_HINT_DAYS]\n        if close:\n            b = min(close, key=near)\n',
            '        close = [b for b in bills if b["_skey"] == canon and likely(b) and gap(b) <= S439_HINT_DAYS and b["id"] not in no]\n        if close:\n            b = min(close, key=near)\n'
            '            s["_likely"] = b["id"]\n', "_why_s439: close amount")
    s = sub(s, '    _prep_s439(scans, bills, ctx)\n    sby = {s["id"]: s for s in scans}\n',
            '    _prep_s439(scans, bills, ctx)\n'
            '    dec = _decisions_s440(con)                                 # S440 (D640): what a person decided about a scan rides every pass\n'
            '    _apply_decisions_s440(scans, dec, ctx)\n'
            '    sby = {s["id"]: s for s in scans}\n', "_rematch: the decisions")
    s = sub(s, '    for r in con.execute("SELECT bill_id, asset_bill_id FROM purchase_scan_link ORDER BY linked_at, bill_id").fetchall():\n'
               '        b, s = bby.get(r[0]), sby.get(r[1])\n'
               '        if b is not None and s is not None and r[1] not in linked and _match_s439(s, b) is not None:\n',
            '    for r in con.execute("SELECT bill_id, asset_bill_id, grade FROM purchase_scan_link ORDER BY linked_at, bill_id").fetchall():\n'
            '        b, s = bby.get(r[0]), sby.get(r[1])\n'
            '        if b is not None and s is not None and r[1] not in linked and (r[2] == "CONFIRMED" or _match_s439(s, b) is not None):   # S440: a person\'s link stays\n',
            "_rematch: a CONFIRMED link stays")
    s = sub(s, "    # 4 · the reason of every scan still open\n    before = {}\n",
            "    for s in scans:                                            # S440: a person recognised this paper as a second scan of a linked one\n"
            "        d = dec.get(s[\"id\"]) or {}\n"
            "        if d.get(\"dup_ok\") and s[\"id\"] not in linked and s[\"id\"] not in dups:\n"
            "            bid = next((bb for bb, sc in taken.items() if sc == d[\"dup_ok\"]), None)\n"
            "            if bid is not None:\n"
            "                dups[s[\"id\"]] = (d[\"dup_ok\"], bid, \"reception confirmed\")\n"
            "    # 4 · the reason of every scan still open\n    before = {}\n", "_rematch: dup by a person")
    s = sub(s, '        con.execute("INSERT OR REPLACE INTO purchase_scan_state (asset_bill_id, why, detail, dup_cand, dup_bill, hint_bill, checked_at) VALUES (?,?,?,?,?,?,?)",\n'
               '                    (sid, why, detail, first, bid, hint, stamp))\n',
            '        _state_put_s440(con, sid, why, detail, first, bid, hint, stamp, s.get("_likely"), dec.get(sid))    # S440: the decisions are written back\n'
            '    for sid, d in dec.items():                                 # S440: a LINKED scan keeps what a person decided about it\n'
            '        if sid in linked and sid in sby:\n'
            '            _state_put_s440(con, sid, "linked", "linked", None, None, None, stamp, None, d)\n', "_rematch: the state row")
    s = sub(s, '    return _page("Scan links", body)\n',
            '    body = _scan_flow_s440(con, body)                          # S440 (D640): the BACK bar, the five groups of Scan ka kaam (read-only), the up-arrow\n'
            '    return _page("Scan links", body)\n', "page_scans: the flow")
    return s


# ----------------------------------------------------------------------------- asset_register.py (PARENT'S, declared)
A_CSS = (
    ".s440bar{position:sticky;top:0;z-index:60;display:flex;align-items:center;gap:12px;background:#1f3864;color:#fff;padding:6px 10px;box-shadow:0 2px 6px rgba(0,0,0,.25)}\n"
    ".s440back{display:flex;align-items:center;justify-content:center;min-height:44px;padding:0 22px;background:#fff;color:#1f3864;border-radius:9px;font-size:18px;font-weight:800;text-decoration:none;white-space:nowrap}\n"
    ".s440name{margin-left:auto;font-weight:600;text-align:right;overflow:hidden;text-overflow:ellipsis}\n"
    "@media (max-width:640px){.s440back{flex:1 1 auto}.s440name{flex:0 1 44%;font-size:14px}}\n"
    "#s440up{position:fixed;right:14px;bottom:18px;width:48px;height:48px;border-radius:24px;border:0;background:#1f3864;color:#fff;font-size:24px;padding:0;display:none;z-index:70;box-shadow:0 2px 8px rgba(0,0,0,.35)}\n"
    ".s440big{display:block;box-sizing:border-box;width:100%;text-align:center;font-size:19px;font-weight:700;padding:15px 10px;margin:10px 0 0;border-radius:10px}\n"
)

A_INTAKE = r'''    return page("""<div id=s440intake style="display:flex;flex-direction:column">
<div class=card style="padding:12px 14px;order:1">
<div style="font-size:17px;font-weight:700"><span id=lane_line>{{lanes[lane_default][0].split(' — ')[0]}} · {{month_label(months[0])}}</span>
<a href="#" id=lane_badlo style="font-weight:400;font-size:14px;margin-left:6px" onclick="var x=document.getElementById('lanebox');x.style.display=(x.style.display==='none'?'block':'none');return false">— badlo</a></div>
<p class=muted id=pf_note style="margin:4px 0 0"></p></div>
<script>function _laneLine(){var s=document.getElementById('intake_lane'),m=document.getElementById('intake_month'),l=document.getElementById('lane_line');if(!s||!m||!l){return;}
l.textContent=s.options[s.selectedIndex].text.split(' — ')[0]+' · '+m.options[m.selectedIndex].text.replace(' (this month)','');}</script>
<script>window.SCANNER_CONFIG = {{ scan_cfg|tojson }};</script>
<div id=scanroot style="order:3"></div>
<div class=card id=lanebox style="display:none;order:2">
<label for=intake_lane style="margin-top:0">What kind of bill is this?</label>
<select id=intake_lane style="max-width:300px"
 onchange="if(window.SCANNER_CONFIG){window.SCANNER_CONFIG.uploadFields.lane=this.value;
             /* S219: >95% of pharmacy purchase bills are half A4 (owner, measured).
                Telling the scanner the page it is looking for is what stops it
                outlining the PRINTING instead of the paper. Cleared for clinic
                bills, which are any shape at all. */
             if(this.value==='pharmacy'){window.SCANNER_CONFIG.expectAspect=0.7048;
               window.SCANNER_CONFIG.expectLabel='half-A4 bill';}
             else{delete window.SCANNER_CONFIG.expectAspect;
               delete window.SCANNER_CONFIG.expectLabel;}}
           var h=document.getElementById('lane_basic'); if(h){h.value=this.value;} _laneLine();">
{% for k in lane_order %}<option value="{{k}}" {{'selected' if k==lane_default}}>{{lanes[k][0]}}</option>{% endfor %}
</select>
<label for=intake_month>Which month is this bill from? <span class=muted>(bill kis mahine ka hai)</span></label>
<select id=intake_month style="max-width:300px"
 onchange="if(window.SCANNER_CONFIG){window.SCANNER_CONFIG.uploadFields.bill_month=this.value;}
           var h=document.getElementById('month_basic'); if(h){h.value=this.value;} _laneLine();">
{% for ym in months %}<option value="{{ym}}" {{'selected' if ym==months[0]}}>{{month_label(ym)}}{{' (this month)' if loop.first else ''}}</option>{% endfor %}
</select></div></div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
<script src="{{ widget_url }}"></script>
<noscript><div class=card>The scanner needs JavaScript — please use the basic upload below.</div></noscript>
<div class=card><label for=intake_note style="margin-top:0">Note <span class=muted>(optional, e.g. "2 boxes, one bill")</span></label>
<input id=intake_note maxlength=120 style="max-width:300px"
 oninput="if(window.SCANNER_CONFIG){window.SCANNER_CONFIG.uploadFields.note=this.value;}"></div>
<details class=card id=kaise><summary style="cursor:pointer;color:#3a5a78;font-weight:600">Kaise? ▾</summary>
<p class=muted>Photograph the paper bill — the scanner squares it up into a
clean PDF (add more pages if the bill runs over). You'll get a <b>stamp number</b>; write it on
the paper bill, then file it. That's all.</p>
<p class=muted style="margin:4px 0 0">Only a clinic bill goes to the approval list. Pharmacy, lab, expense and other documents are
filed as a scan and a stamp. A paper that already carries a B-number is never scanned again — the server catches a double scan.</p>
<p class=muted style="margin:4px 0 0">Old bills from last month? Choose last month first — the accountants' pack for that month then carries them.</p></details>
<details class=card><summary style="cursor:pointer;color:#3a5a78;font-weight:600">📁 Basic upload (no scanner)</summary>
<form method=post action="{{url_for('intake_submit')}}" enctype=multipart/form-data style="margin-top:12px">
<input type=hidden name=lane id=lane_basic value="{{lane_default}}"><input type=hidden name=bill_month id=month_basic value="{{months[0]}}"><input type=hidden name=from value="{{frm or ''}}">
<input type=hidden name=vendor id=pf_vendor><input type=hidden name=bill_no id=pf_bill_no><input type=hidden name=bill_date id=pf_bill_date><input type=hidden name=amount id=pf_amount>
<label class=btn style="cursor:pointer;display:inline-block;position:relative">📷 Take a photo of the bill<input type=file name=bill_cam accept="image/*" capture=environment onchange="_pick(this,'cam_st')" style="position:absolute;width:1px;height:1px;opacity:0;overflow:hidden"></label>
<span id=cam_st class=muted style="margin-left:8px"></span>
<br><br>
<label class="btn small" style="cursor:pointer;display:inline-block;position:relative">📁 Choose a saved photo / PDF<input type=file name=bill_file accept="image/*,.pdf" onchange="_pick(this,'file_st')" style="position:absolute;width:1px;height:1px;opacity:0;overflow:hidden"></label>
<span id=file_st class=muted style="margin-left:8px"></span>
<label>Note <span class=muted>(optional)</span></label>
<input name=note maxlength=120 style="max-width:280px">
<br><button class=btn>Submit bill</button></form>
<script>function _pick(i,s){var e=document.getElementById(s);e.textContent=i.files&&i.files.length?('✓ '+i.files[0].name):'';}</script></details>
<script>(function(){var f=(window.SCANNER_CONFIG||{}).uploadFields||{};var s=document.getElementById('intake_lane');if(f.lane&&s){s.value=f.lane;if(s.onchange)s.onchange();}
var mm=document.getElementById('intake_month');if(mm&&f.bill_month){mm.value=f.bill_month;var hb=document.getElementById('month_basic');if(hb){hb.value=f.bill_month;}}
['vendor','bill_no','bill_date','amount'].forEach(function(k){var e=document.getElementById('pf_'+k);if(e&&f[k]){e.value=f[k];}});
if(f.vendor){var p=document.getElementById('pf_note');if(p){p.textContent='Bill: '+f.vendor+(f.bill_no?' · no. '+f.bill_no:'')+(f.amount?' · ₹'+f.amount:'')+' — filled in from Purchase orders';}}
_laneLine();})();</script>
{{today_html}}""",
        scan_cfg=scan_cfg, widget_url=widget_url, lanes=LANES, lane_order=LANE_ORDER, lane_default=_lane_default,
        months=_months, month_label=_month_label, frm=frm, today_html=_today_html(db),
        flow=_flow(_intake_name_s440(scan_cfg["uploadFields"])))       # S440: the camera first; the kind and the month behind "badlo"; the text under "Kaise?"
'''

A_SLIP = r'''    frm = _safe_from(request.args.get("from"))                    # S440: the Save card
    _lane = b["lane"] or KIND_LANE.get(b["kind"], "clinic")
    back_url = frm or (_site(S440_LIST_PATH) if _lane == "pharmacy" else url_for("bills_list"))
    next_url = url_for("intake", lane=_lane, **({"from": frm} if frm else {}))
    return page("""<div class=card style="max-width:520px;margin:18px auto;text-align:center{{'' if b['dup_of'] else ';background:#e4f2e6;border:2px solid #2e7d5b'}}" id=slipcard>
{% if b['dup_of'] %}<p style="font-size:20px;font-weight:700;color:#b23b3b">{{dup_msg}}</p>
<div style="font-size:64px;font-weight:800;letter-spacing:3px;color:#1f3864">{{first_stamp}}</div>
<p class=muted>Is scan ka number {{b['stamp_no']}} khaali chhod diya gaya (void). Kaagaz par <b>{{first_stamp}}</b> hi likhein.</p>
{% else %}<p style="font-size:22px;font-weight:800;color:#2e6b34;margin:2px 0">Ho gaya — <span id=slipstamp style="display:block;font-size:56px;letter-spacing:2px;color:#1f3864;line-height:1.15">{{b['stamp_no']}}</span> · bill par likh do</p>
<p class=muted id=slipnote><b>{{b['submitted_by']}}</b> · {{b['submitted_at']}} · {{lanes[b['lane'] or 'clinic'][0].split(' — ')[0]}}</p>
<script>(function(){var n=0,t=setInterval(function(){n++;fetch('{{url_for('intake_slip',bid=b['id'])}}?json=1',{cache:'no-store'}).then(function(r){return r.json()}).then(function(j){
 if(j.dup_of){clearInterval(t);var c=document.getElementById('slipcard');if(c){c.style.background='';c.style.border='';c.innerHTML='<p style="font-size:20px;font-weight:700;color:#b23b3b">'+j.message+'</p><div style="font-size:64px;font-weight:800;letter-spacing:3px;color:#1f3864">'+j.first_stamp+'</div><p class=muted>Is scan ka number '+j.stamp+' khaali chhod diya gaya (void). Kaagaz par <b>'+j.first_stamp+'</b> hi likhein.</p><a class="btn s440big" href="{{next_url}}" style="background:#2e7d5b">Agla bill scan karo</a><a class="btn s440big" href="{{back_url}}" style="background:#fff;color:#1f3864;border:2px solid #1f3864">← BACK to the list</a>';}}
 else if(j.ocr_status&&j.ocr_status!=='reading'){clearInterval(t);}
 if(n>=12)clearInterval(t);}).catch(function(){});},2500);})();</script>
{% endif %}<a class="btn s440big" href="{{next_url}}" style="background:#2e7d5b">Agla bill scan karo</a>
<a class="btn s440big" href="{{back_url}}" style="background:#fff;color:#1f3864;border:2px solid #1f3864">← BACK to the list</a></div>
{{today_html}}""", b=b, lanes=LANES, first_stamp=first_stamp, dup_msg=(LANE_SLIP_HI % first_stamp), next_url=next_url, back_url=back_url,
        today_html=_today_html(get_db()), flow=_flow("Scan ho gaya", back_url))
'''


def patch_asset(s):
    s = sub(s, 'APP_VERSION = "1.12.0"  # S409 (D625, 26-Sep-2026): ',
            'APP_VERSION = "1.13.0"  # S440 (D640, 30-Sep-2026): the scan flow for staff -- the BACK bar and the up-arrow on every page of the flow, the intake camera-first, '
            'the Save card, a scanning login\'s own list and bill in staff words, the scan thumbnail, "Galat lane". 1.12.0 -- S409 (D625, 26-Sep-2026): ', "version")
    s = sub(s, "# ---------------------------------------------------------------- templates\nBASE = \"\"\"<!doctype html><html><head><meta charset=utf-8>\n",
            block("asset_block_s440.py", "# ----")
            + "# ---------------------------------------------------------------- templates\nBASE = \"\"\"<!doctype html><html><head><meta charset=utf-8>\n", "the S440 block")
    s = sub(s, ".grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px}\n</style></head><body>\n<header><div><b>🗂 Asset Register</b>",
            ".grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px}\n" + A_CSS + "</style></head><body>\n"
            "{% if flow %}<div class=s440bar><a class=s440back href=\"{{flow.back}}\">← BACK</a><span class=s440name>{{flow.name}}</span></div>{% endif %}\n"
            "{% if not (flow and user and user['role']=='reception') %}<header><div><b>🗂 Asset Register</b>", "BASE: the bar")
    s = sub(s, "<a href=\"{{url_for('logout')}}\">Logout</a>{% endif %}{% endif %}</nav></header>\n",
            "<a href=\"{{url_for('logout')}}\">Logout</a>{% endif %}{% endif %}</nav></header>{% endif %}\n", "BASE: the menu")
    s = sub(s, "{{body}}</main></body></html>\"\"\"\n",
            "{{body}}</main>{% if flow %}<button id=s440up aria-label=\"back to top\" onclick=\"window.scrollTo({top:0,behavior:'smooth'})\">↑</button>\n"
            "<script>window.addEventListener('scroll',function(){var b=document.getElementById('s440up');if(b){b.style.display=(window.pageYOffset>window.innerHeight)?'block':'none';}});</script>{% endif %}"
            "</body></html>\"\"\"\n", "BASE: the up-arrow")
    s = sub(s, "def page(body_tpl, **ctx):\n    u = current_user()\n",
            "def page(body_tpl, **ctx):\n    u = current_user()\n"
            "    flow = ctx.pop(\"flow\", None)                               # S440: a page of the scan flow carries the BACK bar and the up-arrow\n", "page(): flow")
    s = sub(s, "    return render_template_string(BASE, user=u, body=Markup(body), version=APP_VERSION,\n                                  palette_bg=PALETTES[pal][1])\n",
            "    return render_template_string(BASE, user=u, body=Markup(body), version=APP_VERSION,\n                                  palette_bg=PALETTES[pal][1], flow=flow)\n", "page(): render")
    s = sub(s, "@app.route(\"/bills\")\n@checker_required\ndef bills_list():\n    db = get_db()\n",
            "@app.route(\"/bills\")\n@scan_reader\ndef bills_list():\n"
            "    if g.user[\"role\"] == \"reception\":                          # S440: a scanning login's own list, in staff words\n"
            "        return _bills_list_staff()\n"
            "    db = get_db()\n", "bills_list: the staff list")
    s = sub(s, "        bills=bills, q=q, fk=fk, fs=fs, npend=npend, lanes=LANES, lane_order=LANE_ORDER,\n",
            "        bills=bills, q=q, fk=fk, fs=fs, npend=npend, lanes=LANES, lane_order=LANE_ORDER, flow=_flow(\"Purchases\"),\n", "bills_list: flow")
    s = sub(s, "@app.route(\"/bills/<int:bid>/file\")\n@checker_required\ndef bill_file(bid):\n"
               "    b = get_db().execute(\"SELECT source_stored, source_orig FROM bills WHERE id=?\", (bid,)).fetchone()\n"
               "    if not b or not b[\"source_stored\"]:\n        abort(404)\n",
            "@app.route(\"/bills/<int:bid>/file\")\n@scan_reader\ndef bill_file(bid):\n"
            "    b = get_db().execute(\"SELECT source_stored, source_orig, kind, lane, status, submitted_by FROM bills WHERE id=?\", (bid,)).fetchone()\n"
            "    if not b or not b[\"source_stored\"]:\n        abort(404)\n"
            "    if not _staff_may_see(b, image=True):                        # S440: a scanning login -- its own scans, and any live pharmacy scan\n"
            "        abort(403)\n", "bill_file")
    s = sub(s, "@app.route(\"/bills/<int:bid>\")\n@checker_required\ndef bill_view(bid):\n",
            "@app.route(\"/bills/<int:bid>\")\n@scan_reader\ndef bill_view(bid):\n", "bill_view: reader")
    s = sub(s, "    blank = not (b[\"vendor\"] or b[\"total_amount\"] or items)\n",
            "    if g.user[\"role\"] == \"reception\":                          # S440: read-only, and only what this login scanned itself\n"
            "        if not _staff_may_see(b):\n"
            "            abort(403)\n"
            "        return _bill_view_staff(b, items)\n"
            "    blank = not (b[\"vendor\"] or b[\"total_amount\"] or items)\n", "bill_view: the staff page")
    s = sub(s, "        b=b, items=items, sarvam_on=_sarvam_on(), blank=blank, lanes=LANES, lane_order=LANE_ORDER,\n",
            "        b=b, items=items, sarvam_on=_sarvam_on(), blank=blank, lanes=LANES, lane_order=LANE_ORDER,\n"
            "        flow=_flow(\"Bill \" + (b[\"stamp_no\"] or (\"#%d\" % bid)), url_for(\"bills_list\")),\n", "bill_view: flow")
    s = sub(s, "@app.route(\"/bills/<int:bid>/lane\", methods=[\"POST\"])\n@checker_required\ndef bill_lane(bid):\n",
            "@app.route(\"/bills/<int:bid>/lane\", methods=[\"POST\"])\n@scan_reader\ndef bill_lane(bid):\n", "bill_lane: reader")
    s = sub(s, "    to = _lane_key(request.form.get(\"lane\"))\n    frm = b[\"lane\"] or KIND_LANE.get(b[\"kind\"], \"clinic\")\n",
            "    to = _lane_key(request.form.get(\"lane\"))\n    frm = b[\"lane\"] or KIND_LANE.get(b[\"kind\"], \"clinic\")\n"
            "    if g.user[\"role\"] == \"reception\":                          # S440 \"Galat lane\": a captured pharmacy scan, out of the pharmacy lane -- nothing else\n"
            "        if frm != \"pharmacy\" or b[\"status\"] != \"captured\" or to not in S440_STAFF_LANES:\n"
            "            abort(403)\n"
            "        kind, status = _lane_kind_status(to)\n"
            "        db.execute(\"UPDATE bills SET lane=?, kind=?, status=? WHERE id=?\", (to, kind, status, bid))\n"
            "        _audit_bill(db, bid, \"relane\", {\"from\": frm, \"to\": to, \"status\": status, \"via\": \"Scan ka kaam\"})\n"
            "        db.commit()\n"
            "        return redirect(_safe_from(request.form.get(\"back\")) or _site(S440_LIST_PATH))\n", "bill_lane: the staff re-lane")
    s = sub(s, "</select>\n<button class=\"btn small\">Save</button></form></div>\"\"\", rows=rows, seeded=seeded, lanes=LANES, order=LANE_ORDER)\n",
            "</select>\n<button class=\"btn small\">Save</button></form></div>\"\"\", rows=rows, seeded=seeded, lanes=LANES, order=LANE_ORDER,\n"
            "                flow=_flow(\"Scan lanes\", url_for(\"bills_list\")))\n", "lanes_admin: flow")
    s = span(s, "    me = g.user[\"display_name\"]\n    if g.user[\"role\"] == \"reception\":\n        mine = db.execute(\"SELECT id,stamp_no,submitted_at,status FROM bills \"\n",
             "                          \"WHERE stamp_no IS NOT NULL ORDER BY id DESC LIMIT 30\").fetchall()\n",
             "    frm = _safe_from(request.args.get(\"from\"))                  # S440: where BACK and the Save card's \"BACK to the list\" return\n", "intake: from")
    s = sub(s, "        \"backUrl\": url_for(\"intake_slip_last\"),\n",
            "        \"backUrl\": url_for(\"intake_slip_last\", **({\"from\": frm} if frm else {})),     # S440: the slip keeps the way back\n", "intake: backUrl")
    s = span(s, "    return page(\"\"\"<h2>🧾 Scan a new purchase bill</h2>\n",
             "        mine=mine, scan_cfg=scan_cfg, widget_url=widget_url, lanes=LANES, lane_order=LANE_ORDER, lane_default=_lane_default,\n"
             "        months=_months, month_label=_month_label)\n", A_INTAKE, "intake: the page")
    s = sub(s, "        return redirect(url_for(\"intake\"))\n    return redirect(url_for(\"intake_slip\", bid=bid))\n\n@app.route(\"/intake/scan_submit\", methods=[\"POST\"])\n",
            "        return redirect(url_for(\"intake\"))\n"
            "    _frm = _safe_from(request.form.get(\"from\"))                  # S440\n"
            "    return redirect(url_for(\"intake_slip\", bid=bid, **({\"from\": _frm} if _frm else {})))\n\n@app.route(\"/intake/scan_submit\", methods=[\"POST\"])\n", "intake_submit: from")
    s = sub(s, "    if not bid:\n        return redirect(url_for(\"intake\"))\n    return redirect(url_for(\"intake_slip\", bid=bid))\n\n@app.route(\"/intake/slip/<int:bid>\")\n",
            "    _frm = _safe_from(request.args.get(\"from\"))                  # S440\n"
            "    if not bid:\n        return redirect(url_for(\"intake\", **({\"from\": _frm} if _frm else {})))\n"
            "    return redirect(url_for(\"intake_slip\", bid=bid, **({\"from\": _frm} if _frm else {})))\n\n@app.route(\"/intake/slip/<int:bid>\")\n", "intake_slip_last: from")
    s = span(s, "    return page(\"\"\"<div class=card style=\"max-width:430px;margin:26px auto;text-align:center\" id=slipcard>\n",
             "        dup_msg=(LANE_SLIP_HI % first_stamp))\n", A_SLIP, "the slip: the Save card")
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--finance", required=True)
    ap.add_argument("--assetapp", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    for base, name, fn in ((a.finance, "porders.py", patch_porders), (a.finance, "porders.html", patch_porders_html),
                           (a.finance, "purchase_app.py", patch_purchase_app), (a.assetapp, "asset_register.py", patch_asset)):
        src = load(os.path.join(base, name), name)
        raw = fn(src).encode("utf-8")
        open(os.path.join(a.out, name), "wb").write(raw)
        print("%s  %s" % (md5(raw), name))


if __name__ == "__main__":
    main()
