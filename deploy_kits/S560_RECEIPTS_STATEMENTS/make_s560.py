#!/usr/bin/env python3
"""make_s560.py -- S560_RECEIPTS_STATEMENTS: the four edited files rebuilt from the pinned live bytes.

    python3 make_s560.py <dir with the live sorting_desk.py, clinic_papers.py, asset_register.py, packs.py> <out dir>

Exact counted edits (BUILD_NORM_v1): refuses when an input is not at its FROM pin or an anchor is not found exactly the counted
number of times. Every byte of each built file comes from the live file plus these edits (and the kit's two blocks, read here,
never imported). packs.py (THE PARENT'S): edits inside build_bundle and the item-8 list only. No new file on the box.
FIX1 (15-Oct-2026): B1 a payment recorded once (s560_sd_block.txt, s560_js.txt, the allocation table's voided rows); C1 a ticked
construction bill only in 8.4 (PK1); C3 the old Approve refuses a receipt / statement (AR4)."""
import hashlib, os, sys

FROM = {"sorting_desk.py": "a59fa38d7c7f145c8fefa52bad5676d1",
        "clinic_papers.py": "80e3cd8d2ef8e8953b2ae3fec3f85203",
        "asset_register.py": "20ef7bc6b44079f3181d9c52519e8b94",
        "packs.py": "d86d351a46a1ba4da7d0e615da0deb1a"}

HERE = os.path.dirname(os.path.abspath(__file__))


def kit_text(name):
    with open(os.path.join(HERE, name), "rb") as fh:
        return fh.read().decode("utf-8")


SD_BLOCK = kit_text("s560_sd_block.txt")
AR_BLOCK = kit_text("s560_ar_block.txt")
JS_BLOCK = kit_text("s560_js.txt")

# ============================================================================================ sorting_desk.py
SD_EDITS = [
    # SD1 -- the mark
    ("ROAD = \"S559\"                 # S559_ONE_ROAD: the one menu on the desk's pages, /desk?open=<id>, every paper row to the desk\n",
     "ROAD = \"S559\"                 # S559_ONE_ROAD: the one menu on the desk's pages, /desk?open=<id>, every paper row to the desk\n"
     "RECEIPTS = \"S560\"             # S560_RECEIPTS_STATEMENTS: Receipt and Statement (never spend), one payment record, the desk on one screen\n", 1),
    # SD2 (item 1) -- the group titles: Clinic expense; My expense -- Dr MK / Dr Bhawna
    ("    (\"Clinic\", ((\"implant_stock\", \"Implant stock\"), (\"clinic_equipment\", \"Clinic equipment\"),\n",
     "    (\"Clinic expense\", ((\"implant_stock\", \"Implant stock\"), (\"clinic_equipment\", \"Clinic equipment\"),      # S560 item 1\n", 1),
    ("    (\"Personal\", ((\"pe\", \"Personal expense\"), (\"personal\", \"Personal (you only)\"))),\n",
     "    (\"My expense — Dr MK / Dr Bhawna\", ((\"pe\", \"Personal expense\"), (\"personal\", \"Personal (you only)\"))),      # S560 item 1\n", 1),
    # SD3 (item 2) -- the paper kinds
    ("KINDS = ((\"bill\", \"Bill\"), (\"estimate\", \"Estimate slip\"), (\"challan\", \"Challan\"))\n",
     "KINDS = ((\"bill\", \"Bill\"), (\"estimate\", \"Estimate slip\"), (\"challan\", \"Challan\"), (\"receipt\", \"Receipt\"), (\"statement\", \"Statement\"))      # S560\n", 1),
    # SD4 (items 5, 6) -- the database: bills.to_accountant; paper_payment, paper_payment_bill (fingerprinted)
    ("BILL_COLS = ((\"paid_on\", \"TEXT\"), (\"paid_amount\", \"REAL\"))\n",
     "BILL_COLS = ((\"paid_on\", \"TEXT\"), (\"paid_amount\", \"REAL\"), (\"to_accountant\", \"INTEGER NOT NULL DEFAULT 0\"))      # S560 item 6\n", 1),
    ("    \"CREATE TABLE IF NOT EXISTS desk_audit(id INTEGER PRIMARY KEY, at TEXT NOT NULL, who TEXT, action TEXT NOT NULL, detail TEXT)\",\n)\n",
     "    \"CREATE TABLE IF NOT EXISTS desk_audit(id INTEGER PRIMARY KEY, at TEXT NOT NULL, who TEXT, action TEXT NOT NULL, detail TEXT)\",\n"
     "    # S560 item 5: ONE payment record, append-only (a mistake is voided); every bill reference with its fingerprint (S557)\n"
     "    \"CREATE TABLE IF NOT EXISTS paper_payment(id INTEGER PRIMARY KEY, paid_on TEXT NOT NULL, amount REAL NOT NULL, mode TEXT NOT NULL \"\n"
     "    \"CHECK(mode IN ('cash','cheque','bank')), ref TEXT NOT NULL DEFAULT '', proof_bill_id INTEGER, proof_created_at TEXT NOT NULL DEFAULT '', \"\n"
     "    \"by_whom TEXT, at TEXT, voided_at TEXT NOT NULL DEFAULT '', voided_by TEXT NOT NULL DEFAULT '')\",\n"
     "    # FIX1 B1: a re-save changes the payment -- its old allocation rows are voided (kept) and new ones written; one live row per bill\n"
     "    \"CREATE TABLE IF NOT EXISTS paper_payment_bill(payment_id INTEGER NOT NULL, bill_id INTEGER NOT NULL, bill_created_at TEXT NOT NULL DEFAULT '', \"\n"
     "    \"amount REAL NOT NULL, voided_at TEXT NOT NULL DEFAULT '', voided_by TEXT NOT NULL DEFAULT '', PRIMARY KEY(payment_id, bill_id, voided_at))\",\n)\n", 1),
    # SD5 (item 7) -- Waiting: a receipt / statement never 'a bill -- this supplier has open challans'; the papers to put right on top
    ("                if (b[\"doc_kind\"] or \"\") != \"challan\" and _key(b[\"vendor\"]) in sup_wait:\n",
     "                if (b[\"doc_kind\"] or \"\") not in (\"challan\", \"receipt\", \"statement\") and _key(b[\"vendor\"]) in sup_wait:      # S560\n", 1),
    ("        if why:\n            out.append((b, why))\n    return out\n",
     "        if why:\n            out.append((b, why))\n    return _s560_with_fixes(db, owner, out, today)      # S560 item 7: the papers to put right, on top\n", 1),
    ("def _hint(db, b, why):\n",
     "def _hint(db, b, why):\n"
     "    fx = _s560_fix_hint(db, b, why)                                 # S560 item 7: the reason, in the list\n"
     "    if fx:\n"
     "        return fx\n", 1),
    # SD6 (item 2) -- the kind pre-chosen from Claude's reading (receipt / statement only when the reader's kind allows it)
    ("    kind_from = \"paper\" if kind in (\"bill\", \"estimate\", \"challan\") else \"\"\n",
     "    kind_from = \"paper\" if kind in (\"bill\", \"estimate\", \"challan\", \"receipt\", \"statement\") else \"\"      # S560\n", 1),
    ("        if rd and CLAUDE_KIND.get(rd.get(\"doc_kind\") or \"\"):\n            kind, kind_from = CLAUDE_KIND[rd[\"doc_kind\"]], \"Claude's reading\"\n"
     "        elif mode in (\"monthly\", \"sometimes\"):\n",
     "        rk, rblock = _s560_claude_kind(db, b, rd)                   # S560 item 2\n"
     "        if rk:\n            kind, kind_from = rk, \"Claude's reading\"\n"
     "        elif rblock:\n            pass\n"
     "        elif mode in (\"monthly\", \"sometimes\"):\n", 1),
    ("                                                            and b[\"status\"] == \"draft\") else \"\")}\n",
     "                                                            and b[\"status\"] == \"draft\") else \"\"),\n"
     "            **_s560_paper(db, b, owner, rd, today)}                    # S560: paid state, receipt / statement lists, the fix\n", 1),
    # SD7 (items 3, 4, 5, 6) -- the Save: the receipt / statement / Paid? checked first; filed, never accepted; recorded after
    ("def _doc_kind(db, b, k, mode):\n    if k not in (\"bill\", \"estimate\", \"challan\"):\n",
     "def _doc_kind(db, b, k, mode):\n    if k not in (\"bill\", \"estimate\", \"challan\", \"receipt\", \"statement\"):      # S560\n", 1),
    ("    if dest not in DEST_NAME:\n        raise DeskError(\"Choose where it goes.\")\n",
     "    dest, s560 = _s560_pre(db, b, p, dest, owner, today)           # S560: a receipt / statement is filed with the bill it pays\n"
     "    if dest not in DEST_NAME:\n        raise DeskError(\"Choose where it goes.\")\n", 1),
    ("    AR._audit_bill(db, bid, \"desk_saved\", {\"dest\": dest, \"kind\": k_new or None, \"via\": \"desk\"})   # first: a hold written below is newer\n",
     "    AR._audit_bill(db, bid, \"desk_saved\", {\"dest\": dest, \"kind\": k_new or None, \"via\": \"desk\", \"s560\": 1})   # first: a hold written below is newer\n", 1),
    ("    b = _row(db, bid)\n    if accept and _lane(b) == \"clinic\" and b[\"status\"] == \"draft\":\n",
     "    accept = accept and not s560.get(\"no_accept\")                 # S560: a receipt / statement is never accepted as a bill\n"
     "    b = _row(db, bid)\n    if accept and _lane(b) == \"clinic\" and b[\"status\"] == \"draft\":\n", 1),
    ("    b = _row(db, bid)\n    return {\"message\": \"%s → %s.%s\" % (st, DEST_NAME[dest], (\" \" + \" \".join(msgs)) if msgs else \"\"),\n",
     "    msgs += _s560_post(db, bid, p, s560, status0)                   # S560: filed, the payment, the construction tick\n"
     "    b = _row(db, bid)\n    return {\"message\": \"%s → %s.%s\" % (st, DEST_NAME[dest], (\" \" + \" \".join(msgs)) if msgs else \"\"),\n", 1),
    # SD8 (item 7) -- Bills awaited's items line: the items, not the dict's own method
    ("<div style=\"font-size:13px;color:#3d4a57;margin-top:3px\">{{r.items}}</div>",
     "<div style=\"font-size:13px;color:#3d4a57;margin-top:3px\">{{r['items']}}</div>", 1),
    # SD9 (item 5) -- the implant ledger: a receipt / statement is never owed; the S560 payments in its Paid, each once
    ("        else:\n            kind, owed = (\"Estimate slip\" if dk == \"estimate\" else \"Bill\"), b[\"total_amount\"]\n",
     "        elif dk in (\"receipt\", \"statement\"):                         # S560: never owed -- the bill is\n"
     "            kind = \"Receipt\" if dk == \"receipt\" else \"Statement\"\n"
     "        else:\n            kind, owed = (\"Estimate slip\" if dk == \"estimate\" else \"Bill\"), b[\"total_amount\"]\n", 1),
    ("    try:\n        pays = db.execute(\"SELECT * FROM implant_payment ORDER BY day, id\").fetchall()\n",
     "    _s560_ledger(db, rows, sups)                                    # S560 item 5\n"
     "    try:\n        pays = db.execute(\"SELECT * FROM implant_payment ORDER BY day, id\").fetchall()\n", 1),
    # SD10 (items 5, 6) -- the month: paid / unpaid per section; the Construction card's count for the accountant
    ("        noamt = len([b for b in paid_rows if b[\"total_amount\"] is None])\n",
     "        papers += _s560_month_bits(db, key, paid_rows, pm560)          # S560\n"
     "        noamt = len([b for b in paid_rows if b[\"total_amount\"] is None])\n", 1),
    ("    secs = []\n    cache = {}\n",
     "    secs = []\n    cache = {}\n    pm560 = paid_map(db)                                             # S560\n", 1),
    # SD11 (item 1) -- the desk on one laptop screen: compact CSS
    ("#right{width:400px;flex:none;", "#right{width:clamp(440px,45vw,640px);flex:none;", 1),
    ("#left{width:250px;flex:none;", "#left{width:220px;flex:none;", 1),
    ("#fields{overflow:auto;flex:1;min-height:0;padding:12px 14px;display:flex;flex-direction:column;gap:12px}",
     "#fields{overflow:auto;flex:1;min-height:0;padding:8px 14px;display:flex;flex-direction:column;gap:8px}", 1),
    ("#foot{flex:none;padding:10px 14px 12px;border-top:1px solid #d6dde6;background:#fff;display:flex;flex-direction:column;gap:8px}",
     "#foot{flex:none;padding:6px 14px 8px;border-top:1px solid #d6dde6;background:#fff;display:flex;flex-direction:column;gap:5px}", 1),
    (".gt{font-size:11px;letter-spacing:.04em;text-transform:uppercase;color:#5b6878;margin-top:4px}",
     ".gt{font-size:11px;letter-spacing:.04em;text-transform:uppercase;color:#5b6878;margin:1px 0 2px}", 1),
    (".dests{display:flex;flex-wrap:wrap;gap:6px}", ".dests{display:flex;flex-wrap:wrap;gap:4px}", 1),
    (".d{min-height:38px;padding:6px 12px;border-radius:8px;font-size:14px;", ".d{min-height:36px;padding:3px 9px;border-radius:8px;font-size:13px;", 1),
    ("#save{min-height:50px;border-radius:10px;border:0;background:#2b6e4f;color:#fff;font-size:17px;",
     "#save{min-height:44px;border-radius:10px;border:0;background:#2b6e4f;color:#fff;font-size:16px;", 1),
    (".flag{font-size:13px;background:#fff4dc;border:1px solid #e8c77a;border-radius:8px;padding:8px 10px}\n</style></head><body><div id=app>\n",
     ".flag{font-size:13px;background:#fff4dc;border:1px solid #e8c77a;border-radius:8px;padding:8px 10px}\n"
     "#groups{display:flex;flex-wrap:wrap;gap:3px 12px}.grp{display:flex;flex-direction:column}\n"
     "#readbox{border:1px solid #e6ebf0;border-radius:8px;padding:5px 8px}#readbox>summary{cursor:pointer;font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}"
     "#readbox .ed{color:#2b5d8a;text-decoration:underline}\n"
     ".kinds{display:flex;flex-wrap:wrap;gap:4px}.kinds .b{min-height:36px;font-size:13px;padding:3px 9px}\n"
     ".box{flex-direction:column;gap:4px;font-size:13px;background:#f6f8fa;border:1px solid #e1e7ee;border-radius:8px;padding:8px}\n"
     "#right .box .opt{display:flex;gap:6px;align-items:center;font-size:13px;color:#1f2a36}#right .box .opt input{width:auto;display:inline}.box .in{margin-left:22px}\n"
     ".pay{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:6px}#right .pay input{font-size:13px;padding:4px}\n"
     ".modes{display:flex;gap:4px;flex-wrap:wrap}.modes .b{min-height:30px}#paidf>summary{cursor:pointer;font-size:13px;color:#2b5d8a}\n"
     ".paidline{font-size:12px;color:#2b6e4f}#morecue{text-align:center;font-size:12px;color:#2b5d8a;cursor:pointer}#app>.top{padding:5px 18px}\n"
     "</style></head><body><div id=app>\n", 1),
    # SD12 (item 1) -- What was read folds to one line; the kinds; the receipt / statement / Paid? boxes; Send to accountant; the cue
    ("<div style=\"display:flex;flex-direction:column;gap:6px\"><b style=\"font-size:14px\">What was read <span style=\"font-weight:400\" class=muted>— correct anything</span></b>\n<div class=grid2>",
     "<details id=readbox><summary id=readsum><b>Read:</b> — <span class=ed>edit ▾</span></summary><div style=\"display:flex;flex-direction:column;gap:6px;padding-top:6px\">"
     "<b style=\"font-size:13px\">What was read <span style=\"font-weight:400\" class=muted>— correct anything</span></b>\n<div class=grid2>", 1),
    ("<div class=muted style=\"font-size:12px\" id=items></div><div class=muted style=\"font-size:12px\" id=status></div></div>\n",
     "<div class=muted style=\"font-size:12px\" id=items></div></div></details><div class=muted style=\"font-size:12px\" id=status></div>"
     "<div id=paidline class=paidline style=\"display:none\"></div>\n", 1),
    ("<div style=\"display:flex;flex-direction:column;gap:6px\"><b style=\"font-size:14px\">What kind of paper</b>\n<div class=grid3 id=kinds></div><div class=muted style=\"font-size:12px\" id=kindfrom></div>\n",
     "<div style=\"display:flex;flex-direction:column;gap:4px\"><div style=\"display:flex;align-items:center;gap:8px;flex-wrap:wrap\"><b style=\"font-size:13px\">What kind of paper</b>\n<div class=kinds id=kinds></div></div>"
     "<div class=muted style=\"font-size:12px\" id=kindfrom></div><div class=muted style=\"font-size:12px\" id=kindnote></div>\n", 1),
    ("<div class=green id=covers style=\"display:none\"></div></div>\n",
     "<div class=green id=covers style=\"display:none\"></div>\n"
     "<div class=box id=rcpt style=\"display:none\"></div><div class=box id=stmt style=\"display:none\"></div>"
     "<details id=paidf style=\"display:none\"><summary>Paid?</summary><div id=paidbody></div></details></div>\n", 1),
    ("<div style=\"display:flex;flex-direction:column;gap:6px\"><b style=\"font-size:14px\">Where does it go?</b><div id=groups></div>\n",
     "<div style=\"display:flex;flex-direction:column;gap:4px\"><div id=groupsbox><b style=\"font-size:13px\">Where does it go?</b><div id=groups></div></div>"
     "<div id=filedwith class=muted style=\"display:none;font-size:13px\"></div>\n", 1),
    ("<div class=muted style=\"font-size:12px\" id=destnote></div><div id=hints class=muted style=\"font-size:12px\"></div></div>\n",
     "<label id=accbox style=\"display:none;gap:6px;align-items:center;font-size:13px;color:#1f2a36\"><input type=checkbox id=acc style=\"width:auto;display:inline\"> "
     "Send to accountant <span class=muted>(off unless ticked; only a construction bill)</span></label>\n"
     "<div class=muted style=\"font-size:12px\" id=destnote></div><div id=hints class=muted style=\"font-size:12px\"></div></div>\n", 1),
    ("</div><div id=foot><div id=pagebox", "</div><div id=foot><div id=morecue style=\"display:none\">more ▾</div><div id=pagebox", 1),
    # SD13 (items 1-7) -- the desk's script
    ("S.ticks={};(j.covers||[]).forEach(function(c){S.ticks[c.id]=!!c.ticked;});draw();drawList();});}",
     "S.ticks={};(j.covers||[]).forEach(function(c){S.ticks[c.id]=!!c.ticked;});s560init(j);draw();drawList();});}", 1),
    ("$('f_vendor').value=j.supplier;$('f_no').value=j.bill_no;$('f_date').value=j.date;$('f_amt').value=j.amount;crs(j);",
     "$('f_vendor').value=j.supplier;$('f_no').value=j.bill_no;$('f_date').value=j.date;$('f_amt').value=j.amount;crs(j);"
     "sumline();$('readbox').open=S.readopen;paidline(j);$('paidbody').innerHTML='';", 1),
    (" var f='';if(j.flags.hold){", " var f=fixb(j);if(j.flags.hold){", 1),
    (" var h='';C.groups.forEach(function(g){h+='<div class=gt>'+esc(g[0])+'</div><div class=dests>';g[1].forEach(function(d){h+='<button type=button class=\"d'+(d[0]=='pe'?' pe':'')+'\" data-d=\"'+d[0]+'\">'+esc(d[1])+'</button>';});h+='</div>';});$('groups').innerHTML=h;\n",
     " var h='';C.groups.forEach(function(g){h+='<div class=grp><div class=gt>'+esc(g[0])+'</div><div class=dests>';g[1].forEach(function(d){if(d[0]=='pe'){h+='<button type=button class=\"d pe\" data-d=pe data-who=mk>Dr MK</button><button type=button class=\"d pe\" data-d=pe data-who=bhawna>Dr Bhawna</button>';}"
     "else{h+='<button type=button class=\"d\" data-d=\"'+d[0]+'\">'+esc(d[1])+'</button>';}});h+='</div></div>';});$('groups').innerHTML=h;\n", 1),
    ("+'\" data-k=\"'+x[0]+'\" style=\"min-height:38px;font-size:14px\">'+esc(x[1])+'</button>';", "+'\" data-k=\"'+x[0]+'\">'+esc(x[1])+'</button>';", 1),
    (" Array.prototype.forEach.call(document.querySelectorAll('#groups .d'),function(b){b.className='d'+(b.getAttribute('data-d')=='pe'?' pe':'')+(S.dest==b.getAttribute('data-d')?' on':'');});\n",
     " Array.prototype.forEach.call(document.querySelectorAll('#groups .d'),function(b){var dd=b.getAttribute('data-d'),w=b.getAttribute('data-who');b.className='d'+(dd=='pe'?' pe':'')+((S.dest==dd&&(!w||S.who==w))?' on':'');});\n", 1),
    (" $('who').style.display=S.dest=='pe'?'flex':'none';", " $('who').style.display='none';", 1),
    (" var pg=$('pg_on').checked&&$('pg_no').value.trim();var fl=S.flag;var ready=!!(S.dest||pg||fl=='same'||fl=='restore');\n"
     " if((j.flags.hold||j.flags.s441)&&!fl){ready=false;}\n"
     " if(fl=='keep'&&!S.dest&&!pg){ready=false;}\n"
     " $('save').disabled=!ready;$('save').textContent=ready?'Save — next paper':((j.flags.hold||j.flags.s441)&&!fl?'Answer the question above':'Choose where it goes');}\n",
     " s560paint(j);paint2();}\n", 1),
    (" else if(t.hasAttribute('data-d')){S.dest=t.getAttribute('data-d');paint();}\n",
     " else if(t.hasAttribute('data-d')){S.dest=t.getAttribute('data-d');if(t.hasAttribute('data-who')){S.who=t.getAttribute('data-who');}paint();}\n", 1),
    (" if($('pg_on').checked&&$('pg_no').value.trim()){b.page_of=$('pg_no').value.trim();b.dest='';}post(b);});\n",
     " s560body(b,j);if($('pg_on').checked&&$('pg_no').value.trim()){b.page_of=$('pg_no').value.trim();b.dest='';}post(b);});\n", 1),
    ("loadList(C.open||0);\n})();\n</script></body></html>\"\"\"", JS_BLOCK + "loadList(C.open||0);\n})();\n</script></body></html>\"\"\"", 1),
    ("\"save\": url_for(\"s551_api_save\"), \"groups\": groups, \"kinds\": [list(k) for k in KINDS], \"notes\": NOTES, \"owner\": owner}\n",
     "\"save\": url_for(\"s551_api_save\"), \"groups\": groups, \"kinds\": [list(k) for k in KINDS], \"notes\": NOTES, \"owner\": owner,\n"
     "           \"fix\": url_for(\"s560_fix\"), \"void\": url_for(\"s560_void\"), \"modes\": [list(m) for m in PAY_MODES],\n"
     "           \"names\": {k: v for k, v in DEST_NAME.items() if (k != \"personal\" or owner)}}      # S560\n", 1),
    # SD14 -- the S560 block, and its two routes
    ("# ---------------------------------------------------------------------------------------------- the mount\n",
     SD_BLOCK + "# ---------------------------------------------------------------------------------------------- the mount\n", 1),
    ("    app.add_url_rule(\"/desk/month\", \"s551_month\", cr(_gate(month_page)))\n",
     "    app.add_url_rule(\"/desk/month\", \"s551_month\", cr(_gate(month_page)))\n"
     "    app.add_url_rule(\"/desk/api/fix\", \"s560_fix\", cr(_gate(fix_answer)), methods=[\"POST\"])                  # S560 item 7\n"
     "    app.add_url_rule(\"/desk/api/payment/void\", \"s560_void\", cr(_gate(pay_void)), methods=[\"POST\"])         # S560 item 5\n", 1),
]

# ============================================================================================ clinic_papers.py
CP_EDITS = [
    ("VERSION = \"S551\"\n", "VERSION = \"S551\"\nRECEIPTS = \"S560\"            # S560: a receipt / statement is never a purchase, never accepted\n", 1),
    # CP1 -- the papers that count (the month's money, the old month page): never a receipt or a statement
    ("    w = (\"COALESCE(%s.lane,'clinic')='clinic' AND %s.status IN ('draft','approved') AND %s.dup_of IS NULL\"\n"
     "         % (alias, alias, alias))\n"
     "    if \"doc_kind\" in _cols(db):\n"
     "        w += \" AND COALESCE(%s.doc_kind,'bill')<>'challan'\" % alias                     # S531: a challan is not a purchase\n",
     "    w = (\"COALESCE(%s.lane,'clinic')='clinic' AND %s.status IN ('draft','approved') AND %s.dup_of IS NULL\"\n"
     "         % (alias, alias, alias))\n"
     "    if \"doc_kind\" in _cols(db):\n"
     "        w += \" AND COALESCE(%s.doc_kind,'bill') NOT IN ('challan','receipt','statement')\" % alias      # S531; S560: nor a receipt / statement\n", 1),
    ("    w = (\"COALESCE(%s.lane,'clinic') IN ('clinic','other_doc','owner_expense') AND %s.status IN ('draft','approved','captured')\"\n"
     "         \" AND %s.dup_of IS NULL\" % (alias, alias, alias))\n"
     "    if \"doc_kind\" in _cols(db):\n"
     "        w += \" AND COALESCE(%s.doc_kind,'bill')<>'challan'\" % alias                     # S531: a challan is not a purchase\n",
     "    w = (\"COALESCE(%s.lane,'clinic') IN ('clinic','other_doc','owner_expense') AND %s.status IN ('draft','approved','captured')\"\n"
     "         \" AND %s.dup_of IS NULL\" % (alias, alias, alias))\n"
     "    if \"doc_kind\" in _cols(db):\n"
     "        w += \" AND COALESCE(%s.doc_kind,'bill') NOT IN ('challan','receipt','statement')\" % alias      # S531; S560: nor a receipt / statement\n", 1),
    # CP2 -- sorted = accepted never takes a receipt / statement; the heal at every start neither; no challan offered to one
    ("        return False                                                 # S551: a challan waits for its bill; it can still be joined\n",
     "        return False                                                 # S551: a challan waits for its bill; it can still be joined\n"
     "    if \"doc_kind\" in b.keys() and (b[\"doc_kind\"] or \"\") in (\"receipt\", \"statement\"):\n"
     "        return False                                                 # S560: a receipt / statement is never accepted as a bill\n", 1),
    ("                          \"AND (COALESCE(b.doc_kind,'bill')<>'challan' OR b.challan_state='final') ORDER BY b.id\").fetchall()\n",
     "                          \"AND (COALESCE(b.doc_kind,'bill')<>'challan' OR b.challan_state='final') \"\n"
     "                          \"AND COALESCE(b.doc_kind,'bill') NOT IN ('receipt','statement') ORDER BY b.id\").fetchall()      # S560\n", 1),
    ("    if not _has_challans(db) or (b[\"lane\"] or \"clinic\") == \"pharmacy\" or (b[\"doc_kind\"] or \"\") == \"challan\":\n",
     "    if not _has_challans(db) or (b[\"lane\"] or \"clinic\") == \"pharmacy\" or (b[\"doc_kind\"] or \"\") in (\"challan\", \"receipt\", \"statement\"):      # S560\n", 1),
]

# ============================================================================================ asset_register.py
AR_EDITS = [
    # AR1 (item 5) -- the old bill page: the paid line under Total
    ("<b>Total:</b> {{'₹%.2f'|format(b['total_amount']) if b['total_amount'] is not none else '—'}}</div>\n<div class=card>{% if b['notes'] %}",
     "<b>Total:</b> {{'₹%.2f'|format(b['total_amount']) if b['total_amount'] is not none else '—'}}{{s560_paid(b) if s560_paid is defined else ''}}</div>\n<div class=card>{% if b['notes'] %}", 1),
    # AR2 (item 5) -- All papers: the small Paid mark beside the total
    ("<td>{{'\\u20b9%.2f'|format(b['total_amount']) if b['total_amount'] is not none else '\\u2014'}}</td></tr>{% endfor %}</table>\n{% if not bills %}",
     "<td>{{'\\u20b9%.2f'|format(b['total_amount']) if b['total_amount'] is not none else '\\u2014'}}{{s560_mark(b) if s560_mark is defined else ''}}</td></tr>{% endfor %}</table>\n{% if not bills %}", 1),
    # AR4 (FIX1 C3) -- the old bill page's Approve: a receipt or a statement is never approved as spend
    ("        flash(\"Only draft bills can be approved.\")\n        return redirect(url_for(\"bill_view\", bid=bid))\n",
     "        flash(\"Only draft bills can be approved.\")\n        return redirect(url_for(\"bill_view\", bid=bid))\n"
     "    if \"doc_kind\" in b.keys() and (b[\"doc_kind\"] or \"\") in (\"receipt\", \"statement\"):      # S560 FIX1 C3: never approved as spend\n"
     "        flash(\"A receipt or a statement is never approved as a bill — the bill it pays is.\")\n"
     "        return redirect(url_for(\"bill_view\", bid=bid))\n", 1),
    # AR3 -- the helpers, after S559's block
    ("app.jinja_env.globals.update(s559_bar=_s559_bar, s559_href=_s559_paper_href, s559_kind=_s559_kind)\n# --- S559_ONE_ROAD end ---\n",
     "app.jinja_env.globals.update(s559_bar=_s559_bar, s559_href=_s559_paper_href, s559_kind=_s559_kind)\n# --- S559_ONE_ROAD end ---\n" + AR_BLOCK, 1),
]

# ============================================================================================ packs.py (THE PARENT'S: build_bundle and the item-8 list only)
PK_EDITS = [
    # PK1 (item 6a, 6b) -- build_bundle: every bundle leaves out a receipt, a statement and an awaiting challan; the new
    #                       "construction_accountant" bundle: construction BILLS marked for the accountant, whatever their lane
    ("        qlane, who_sql = lane, \"\"                                    # S548 (D721): Dr Bhawna's expense file apart from Dr Manoj's\n"
     "        if lane == \"owner_expense_bhawna\":\n",
     "        qlane, who_sql = lane, \"\"                                    # S548 (D721): Dr Bhawna's expense file apart from Dr Manoj's\n"
     "        lane_sql, xk_sql = \"lane=?\", \"\"                             # S560 (D728): construction bills for the accountant, any lane\n"
     "        if \"doc_kind\" in cols:                                       # S560: a receipt / statement is never spend; an awaiting challan waits\n"
     "            xk_sql = \" AND COALESCE(doc_kind,'bill') NOT IN ('receipt','statement')\"\n"
     "            if \"challan_state\" in cols:\n"
     "                xk_sql += \" AND NOT (COALESCE(doc_kind,'')='challan' AND COALESCE(challan_state,'awaiting')<>'final')\"\n"
     "        if lane != \"construction_accountant\" and {\"to_accountant\", \"subgroup\", \"doc_kind\"} <= cols:      # S560 FIX1 C1: a ticked\n"
     "            xk_sql += (\" AND NOT (COALESCE(subgroup,'')='construction' AND COALESCE(doc_kind,'bill')='bill'\"   # construction bill goes\n"
     "                       \" AND COALESCE(to_accountant,0)=1)\")                          # into the pack once: 8.4 only\n"
     "        if lane == \"construction_accountant\":\n"
     "            if \"to_accountant\" not in cols or \"subgroup\" not in cols or \"doc_kind\" not in cols:\n"
     "                return None, \"no construction bill is marked for the accountant yet\"\n"
     "            lane_sql, qlane = \"subgroup=?\", \"construction\"\n"
     "            xk_sql += \" AND COALESCE(doc_kind,'bill')='bill' AND to_accountant=1\"\n"
     "        elif lane == \"owner_expense_bhawna\":\n", 1),
    ("\"SELECT id, stamp_no, vendor, bill_no, bill_date, total_amount, source_stored, late_for, created_at, %s AS bmonth FROM bills WHERE lane=? AND status<>'rejected'%s \"\n"
     "            \"AND ((%s=?) OR (substr(created_at,1,7)=? AND late_for IS NOT NULL AND %s<>?)) ORDER BY late_for IS NOT NULL, bill_date, id\" % (mcol, who_sql, mcol, mcol), (qlane, month, month, month))]\n",
     "\"SELECT id, stamp_no, vendor, bill_no, bill_date, total_amount, source_stored, late_for, created_at, %s AS bmonth FROM bills WHERE %s AND status<>'rejected'%s \"\n"
     "            \"AND ((%s=?) OR (substr(created_at,1,7)=? AND late_for IS NOT NULL AND %s<>?)) ORDER BY late_for IS NOT NULL, bill_date, id\" % (mcol, lane_sql, who_sql + xk_sql, mcol, mcol), (qlane, month, month, month))]\n", 1),
    ("        return None, \"no %s scans for %s\" % ({\"owner_expense_bhawna\": \"Dr Bhawna expense\"}.get(lane, lane.replace(\"_\", \" \")), _month_name(month))   # S548\n",
     "        return None, \"no %s scans for %s\" % ({\"owner_expense_bhawna\": \"Dr Bhawna expense\", \"construction_accountant\": \"construction bill (for the accountant)\"}.get(lane, lane.replace(\"_\", \" \")), _month_name(month))   # S548; S560\n", 1),
    ("            fh.write(_text_pdf(\"%s bills -- %s (%d)\" % ({\"owner_expense_bhawna\": \"Dr Bhawna Expense\"}.get(lane, lane.replace(\"_\", \" \").title()), _month_name(month), len(rows)), idx))   # S548\n",
     "            fh.write(_text_pdf(\"%s bills -- %s (%d)\" % ({\"owner_expense_bhawna\": \"Dr Bhawna Expense\", \"construction_accountant\": \"Construction\"}.get(lane, lane.replace(\"_\", \" \").title()), _month_name(month), len(rows)), idx))   # S548; S560\n", 1),
    # PK2 (item 6b) -- the item-8 list: 8.4 Construction bills marked for the accountant
    ("                                         (\"owner_expense_bhawna\", \"Dr Bhawna's expense-file bills\")), 1):     # S548 (D721)\n",
     "                                         (\"owner_expense_bhawna\", \"Dr Bhawna's expense-file bills\"),\n"
     "                                         (\"construction_accountant\", \"Construction bills marked for the accountant\")), 1):     # S548 (D721); S560 (D728): 8.4\n", 1),
]


def md5(b):
    return hashlib.md5(b).hexdigest()


def build(name, raw, edits):
    if md5(raw) != FROM[name]:
        sys.exit("REFUSED: %s is %s, not the pinned %s" % (name, md5(raw)[:8], FROM[name][:8]))
    s = raw.decode("utf-8")
    for i, (old, new, n) in enumerate(edits, 1):
        c = s.count(old)
        if c != n:
            sys.exit("REFUSED: %s edit %d anchor found %d times, expected %d" % (name, i, c, n))
        s = s.replace(old, new)
    return s.encode("utf-8")


def main():
    src, out = sys.argv[1], sys.argv[2]
    only = sys.argv[3].split(",") if len(sys.argv) > 3 else None
    os.makedirs(out, exist_ok=True)
    for name, edits in (("sorting_desk.py", SD_EDITS), ("clinic_papers.py", CP_EDITS), ("asset_register.py", AR_EDITS), ("packs.py", PK_EDITS)):
        if only and name not in only:
            continue
        raw = open(os.path.join(src, name), "rb").read()
        new = build(name, raw, edits)
        open(os.path.join(out, name), "wb").write(new)
        print("%s %s -> %s (%d counted edits)" % (name, FROM[name][:8], md5(new), len(edits)))


if __name__ == "__main__":
    main()
