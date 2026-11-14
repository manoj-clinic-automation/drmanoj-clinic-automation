#!/usr/bin/env python3
"""make_s835.py -- kit S835_CREDIT_NOTES: builds the four files from their pinned bytes by exact, counted edits.
usage: python3 make_s835.py <base dir> <block dir> <out dir>"""
import hashlib, os, sys

BASE, BLK, OUT = sys.argv[1:4]
PINS = {"sorting_desk.py": "baa7c6aa95acb79eebdf6f983ed55931", "claude_reader.py": "a7df99bb2fa5ac37c248df9e277e2e39",
        "clinic_papers.py": "b8f551c48d1499a9f21f62c26aa947e6", "xray_costs.py": "5823bae246460c3b065179f70137797a"}


def rd(p):
    with open(p, "rb") as f:
        return f.read()


def ed(t, old, new, n=1, what=""):
    c = t.count(old)
    if c != n:
        sys.exit("STOP: %s -- anchor found %d times, %d expected:\n%s" % (what, c, n, old[:160]))
    return t.replace(old, new)


src = {}
for f, pin in PINS.items():
    b = rd(os.path.join(BASE, f))
    if hashlib.md5(b).hexdigest() != pin:
        sys.exit("STOP: %s is not the pinned file %s" % (f, pin[:8]))
    src[f] = b.decode("utf-8")
BLOCK_PY = rd(os.path.join(BLK, "block_sd.py")).decode("utf-8")
BLOCK_JS = rd(os.path.join(BLK, "block_js.txt")).decode("utf-8")

# ------------------------------------------------------------------ sorting_desk.py
t = src["sorting_desk.py"]
E = []
def e(old, new, n=1, what=""):
    global t
    t = ed(t, old, new, n, what)
    E.append(what)

e('PROCROOM_S635 = "S635"        # S635_PROCROOM_ORDERS: his order (counts nothing) and the slip joined to it, chosen in the same panel\n',
  'PROCROOM_S635 = "S635"        # S635_PROCROOM_ORDERS: his order (counts nothing) and the slip joined to it, chosen in the same panel\n'
  'CREDIT_NOTES = "S835"         # S835_CREDIT_NOTES (D986, F-1174): a dealer\'s credit note -- filed against the bill it lowers, never spend\n', what="E01 the version line")
e('KINDS = (("bill", "Bill"), ("estimate", "Estimate slip"), ("challan", "Challan"), ("receipt", "Receipt"), ("statement", "Statement"))      # S560\n',
  'KINDS = (("bill", "Bill"), ("estimate", "Estimate slip"), ("challan", "Challan"), ("receipt", "Receipt"), ("statement", "Statement"),      # S560\n'
  '         ("credit_note", "Credit note"))                                                                                              # S835\n', what="E02 KINDS")
e('CLAUDE_KIND = {"tax_invoice": "bill", "bill": "bill", "estimate": "estimate", "quotation": "estimate", "challan": "challan"}\n',
  'CLAUDE_KIND = {"tax_invoice": "bill", "bill": "bill", "estimate": "estimate", "quotation": "estimate", "challan": "challan",\n'
  '               "credit_note": "credit_note"}                                                                    # S835\n', what="E03 CLAUDE_KIND")
e('    kind_from = "paper" if kind in ("bill", "estimate", "challan", "receipt", "statement") else ""      # S560\n',
  '    kind_from = "paper" if kind in ("bill", "estimate", "challan", "receipt", "statement", "credit_note") else ""      # S560; S835\n', what="E04 paper_json kind_from")
e('            **_s739_paper(db, b, owner, y739)}                                               # S739: the Stationery-page card; Yuvika\n',
  '            **_s739_paper(db, b, owner, y739),                                               # S739: the Stationery-page card; Yuvika\n'
  '            **_s835_paper(db, b, owner, rd, today)}                                          # S835: the credit note box; a bill\'s credit notes\n', what="E05 paper_json S835 part")
e('    if _lane(b) == "pharmacy":\n        return "%s is a pharmacy paper — the Sanjeevni side keeps it; it is not opened on the desk." % _stamp(b)\n',
  '    if _lane(b) == "pharmacy" and not _s835_open(b, owner):          # S835: a credit note handed to Sanjeevni still opens here (desk.cn)\n'
  '        return "%s is a pharmacy paper — the Sanjeevni side keeps it; it is not opened on the desk.%s" % (_stamp(b), _s835_named(b))\n', what="E06 _visible")
e('    if frm == "pharmacy":\n        raise DeskError("A pharmacy paper is never moved off the pharmacy lane from the desk.")\n',
  '    if frm == "pharmacy" and not _s835_is_cn(b):                     # S835: a credit note may be pointed at a clinic bill instead\n'
  '        raise DeskError("A pharmacy paper is never moved off the pharmacy lane from the desk.")\n', what="E07 _relane")
e('    if k not in ("bill", "estimate", "challan", "receipt", "statement"):      # S560\n',
  '    if k not in ("bill", "estimate", "challan", "receipt", "statement", "credit_note"):      # S560; S835\n', what="E08 _doc_kind")
e('    dest, s560 = _s560_pre(db, b, p, dest, owner, today)           # S560: a receipt / statement is filed with the bill it pays\n',
  '    dest, s835 = _s835_pre(db, b, p, dest, owner, today)           # S835: a credit note is filed with the bill it lowers\n'
  '    dest, s560 = _s560_pre(db, b, p, dest, owner, today)           # S560: a receipt / statement is filed with the bill it pays\n', what="E09 save: _s835_pre")
e('    accept = accept and not s560.get("no_accept")                 # S560: a receipt / statement is never accepted as a bill\n',
  '    accept = accept and not s560.get("no_accept") and not s835.get("cn")      # S560: a receipt / statement is never accepted as a bill; S835 nor a credit note\n', what="E10 save: accept")
e('    msgs += _s732_post(db, bid, p, dest)                            # S732: the Other lines (the paper\'s item lines)\n',
  '    msgs += _s732_post(db, bid, p, dest)                            # S732: the Other lines (the paper\'s item lines)\n'
  '    msgs += _s835_post(db, bid, p, s835, status0)                   # S835: the credit note filed, its one live link\n', what="E11 save: _s835_post")
e('''    for r in db.execute("SELECT b.vendor, " + CP.MONTH_OF + " FROM bills b WHERE COALESCE(b.doc_kind,'bill')<>'challan' "''',
  '''    for r in db.execute("SELECT b.vendor, " + CP.MONTH_OF + " FROM bills b WHERE COALESCE(b.doc_kind,'bill') NOT IN ('challan','credit_note') "''', what="E12 _bills_by_month")
e('        elif dk in ("receipt", "statement"):                         # S560: never owed -- the bill is\n',
  '        elif dk == "credit_note":                                    # S835: a credit note lowers what is owed\n'
  '            kind, owed = "Credit note", (-float(b["total_amount"]) if b["total_amount"] is not None else None)\n'
  '        elif dk in ("receipt", "statement"):                         # S560: never owed -- the bill is\n', what="E13 ledger")
e('    out["paid"] = paid\n    out["state"] = _s560_state(b["total_amount"], paid)\n'
  '    out["word"] = {"paid": "Paid", "part": "Part-paid %s of %s" % (_inr(paid), _inr(b["total_amount"])), "unpaid": ""}[out["state"]]\n',
  '    out["paid"] = paid\n    out["credit"] = _s835_credit_sum(db, b)                         # S835: the credit notes against it lower what it owes\n'
  '    out["state"] = _s560_state(b["total_amount"], paid + out["credit"])\n'
  '    out["word"] = {"paid": "Paid" if (paid > 0 or not out["credit"]) else "Nothing owed — credit note",\n'
  '                   "part": (("Part-paid %s of %s" % (_inr(paid), _inr(b["total_amount"])) + ((" · credit note −%s" % _inr(out["credit"])) if out["credit"] else ""))\n'
  '                            if paid > 0 else "Credit note −%s of %s" % (_inr(out["credit"]), _inr(b["total_amount"]))),\n'
  '                   "unpaid": ""}[out["state"]]\n', what="E14 paid_state")
e('''    try:
        return {(r[0], r[1] or ""): (r[2] or 0) for r in db.execute(
            "SELECT a.bill_id, a.bill_created_at, SUM(a.amount) FROM paper_payment_bill a JOIN paper_payment p ON p.id=a.payment_id "
            "WHERE p.voided_at='' AND a.voided_at='' GROUP BY a.bill_id, a.bill_created_at")}
    except sqlite3.Error:
        return {}
''', '''    try:
        m = {(r[0], r[1] or ""): (r[2] or 0) for r in db.execute(
            "SELECT a.bill_id, a.bill_created_at, SUM(a.amount) FROM paper_payment_bill a JOIN paper_payment p ON p.id=a.payment_id "
            "WHERE p.voided_at='' AND a.voided_at='' GROUP BY a.bill_id, a.bill_created_at")}
    except sqlite3.Error:
        m = {}
    for k_, v_ in _s835_credit_map(db).items():                     # S835: a credit note counts toward its bill's paid state
        m[k_] = m.get(k_, 0) + v_
    return m
''', what="E15 paid_map")
e('    if noted and not pids:\n        return None, "Its payment is noted on the paper itself."\n',
  '    if noted and not pids:\n        return None, "Its payment is noted on the paper itself."\n'
  '    if not pids and not noted:                                      # S835: nothing paid -- its credit note covers it\n'
  '        return None, "Nothing is owed on it — its credit note covers it."\n', what="E16 _s560_direct_edit")
e('    return max(0.0, float(b["total_amount"]) - (st["paid"] - _s560_mine(db, pid, b)))\n',
  '    return max(0.0, float(b["total_amount"]) - (st["paid"] + st.get("credit", 0) - _s560_mine(db, pid, b)))      # S835: less its credit notes\n', what="E17 _s560_outstanding")
e('        paid = paid_state(db, r)["paid"] - mine\n',
  '        paid = (lambda ps_: ps_["paid"] + ps_.get("credit", 0))(paid_state(db, r)) - mine      # S835: a credit note lowers what it owes\n', what="E18 _s560_payable")
e('    if was in NOT_SPEND and k in ("bill", "estimate", "challan"):   # FIX2 C4: a receipt / statement turned into a bill (or estimate / challan)\n',
  '    if was in NOT_SPEND and k in ("bill", "estimate", "challan", "credit_note"):   # FIX2 C4: a receipt / statement turned into a bill (or estimate / challan; S835 a credit note)\n', what="E19 _s560_pre unproof")
e('    rd = reading(db, b["id"])\n    if rd and _s560_looks_receipt(db, b, rd):\n',
  '    rd = reading(db, b["id"])\n    cn835 = _s835_fix(db, b, rd, owner)                                    # S835: the reader says credit note\n    if cn835:\n        return cn835\n'
  '    if rd and _s560_looks_receipt(db, b, rd):\n', what="E20 _s560_fix_of")
e('        paid_rows = list(money) + list(finals)\n        total = _s566_total(paid_rows)                               # S566 item 6: the one sum\n',
  '        paid_rows = list(money) + list(finals)\n        cn835 = _s835_cn_rows(db, key, subs, ym)                     # S835: this section\'s credit notes, by their own month\n'
  '        total = _s566_total(paid_rows + list(cn835))                 # S566 item 6: the one sum (S835: less the credit notes)\n', what="E21 month_data total")
e('        secs.append({"key": key, "name": name, "papers": papers, "total": total, ',
  '        secs.append({"key": key, "name": name, "papers": papers, "total": total, "bought": _s566_total(paid_rows), "credit": -_s566_total(list(cn835)),\n'
  '                     "cns": _s835_cn_view(db, cn835), ', what="E22 month_data section")
e('        tot += _s566_total(list(money) + list(finals))\n',
  '        tot += _s566_total(list(money) + list(finals) + list(_s835_cn_rows(db, key, subs, ym)))      # S835: less the credit notes\n', what="E23 month_total")
e('    return sum((b["total_amount"] or 0) for b in paid_rows)\n',
  '    return sum((-1 if (_col(b, "doc_kind") or "") == "credit_note" else 1) * (b["total_amount"] or 0) for b in paid_rows)      # S835: a credit note counts negative\n', what="E24 _s566_total")
e('<div style="border-top:1px solid #eef1f4">\n<div style="display:grid;grid-template-columns:minmax(0,1fr) 110px 120px 140px;gap:8px;padding:8px 14px;font-size:12px;background:#f6f8fa" class=muted><span>Item</span>',
  '<div style="border-top:1px solid #eef1f4">\n'
  '{% if s.credit %}<div id="s835cn-{{s.key}}" style="display:grid;grid-template-columns:minmax(0,1fr) 140px;gap:4px 8px;padding:10px 14px;font-size:14px;border-bottom:1px solid #eef1f4">'
  '<span>{{s.name}} · bought</span><span style="text-align:right">{{inr(s.bought)}}</span>'
  '<span>Credit notes{% for c in s.cns %} · <a href="{{s559_href(c.id) if s559_href is defined else url_for(\'bill_view\',bid=c.id)}}">{{c.stamp}}</a>{% if c.against %} (against {{c.against}}){% endif %}{% endfor %}</span>'
  '<span style="text-align:right;color:#166534">− {{inr(s.credit)}}</span><b>Spent</b><b style="text-align:right">{{inr(s.total)}}</b></div>{% endif %}\n'
  '<div style="display:grid;grid-template-columns:minmax(0,1fr) 110px 120px 140px;gap:8px;padding:8px 14px;font-size:12px;background:#f6f8fa" class=muted><span>Item</span>', what="E25 MONTH_TPL credit lines")
e('.c739{flex-direction:column;gap:6px;',
  '.c835{border:1px solid #e1e7ee;border-radius:8px;padding:6px 8px;background:#fff;display:flex;flex-direction:column;gap:4px}.c835.on{border:2px solid #2b5d8a;background:#fbfdff}.c835 summary{cursor:pointer;font-size:13px;color:#2b5d8a}'
  '.g835{display:flex;gap:10px;flex-wrap:wrap;margin-top:6px}.g835 iframe{width:200px;height:260px;border:1px solid #d6dde6;border-radius:6px;background:#fbfaf7}'
  '.t835{border-collapse:collapse;width:100%;font-size:12px}.t835 th,.t835 td{text-align:left;padding:3px 5px;border-bottom:1px solid #e6ebf0;vertical-align:top}.t835 th{color:#4a5866;font-weight:600;background:#f6f8fa}.t835 .r835{text-align:right}'
  '.y835{font-size:12px;background:#fffbeb;border:1px solid #f3e0a6;border-radius:6px;padding:6px 8px}#right #cn835 label input{display:block;font-size:14px}#right #cn835 .opt input{display:inline;width:auto}\n'
  '.c739{flex-direction:column;gap:6px;', what="E26 desk CSS")
e('<div id=paidline class=paidline style="display:none"></div>',
  '<div id=paidline class=paidline style="display:none"></div><div id=cnon835 style="display:none;font-size:13px"></div>', what="E27 desk: the bill's credit notes")
e('<div class=box id=stmt style="display:none"></div>',
  '<div class=box id=stmt style="display:none"></div><div class=box id=cn835 style="display:none"></div>', what="E28 desk: the credit note box")
e('s634init(j);s732init(j);s571init(j);s715init(j);draw();drawList();});}',
  's634init(j);s732init(j);s571init(j);s715init(j);s835init(j);draw();drawList();});}', what="E29 openPaper: s835init")
e(' s560paint(j);s568paint(j);s634paint(j);s732paint(j);s571paint(j);paint2();}',
  ' s560paint(j);s568paint(j);s634paint(j);s732paint(j);s571paint(j);s835paint(j);paint2();}', what="E30 paint: s835paint")
e(' s560body(b,j);s568body(b,j);s634body(b,j);s732body(b,j);s739body(b,j);',
  ' s560body(b,j);s568body(b,j);s634body(b,j);s732body(b,j);s739body(b,j);s835body(b,j);', what="E31 Save body: s835body")
e("function forced(){if(S.kind=='receipt'){",
  "function forced(){if(S.kind=='credit_note'){return s835forced();}if(S.kind=='receipt'){", what="E32 forced")
e(" if(S.kind=='receipt'){if(!S.rc.pays||S.rc.pays=='st'){return 'Choose the bill it pays';}",
  " if(S.kind=='credit_note'){return s835why();}\n if(S.kind=='receipt'){if(!S.rc.pays||S.rc.pays=='st'){return 'Choose the bill it pays';}", what="E33 s560why")
e("(why&&(S.dest||s560linked())?why:",
  "(why&&(S.dest||s560linked()||S.kind=='credit_note')?why:", what="E34 paint2 words")
e("function fixb(j){if(!j.fix){return j.aside?'<div class=flag id=s563aside><b>'+esc(j.aside.text)+'</b><br><button type=button class=b data-restore=1>Restore</button></div>':'';}var k=j.fix.key,h='<div class=flag id=s560fix><b>'+esc(j.fix.text)+'</b><br>';\n"
  " if(k=='blank'){h+='<button type=button class=b data-fix=restore>Restore</button> <button type=button class=b data-fix=keep>Leave it set aside</button>';}\n"
  " else if(k=='receipt'||k=='statement'){h+='<button type=button class=b data-s560k=\"'+k+'\">Make it a '+(k=='receipt'?'Receipt':'Statement')+'</button> <button type=button class=b data-fix=keep>No — leave it</button>';}\n",
  "function fixb(j){if(!j.fix){return j.aside?'<div class=flag id=s563aside><b>'+esc(j.aside.text)+'</b><br><button type=button class=b data-restore=1>Restore</button></div>':'';}var k=j.fix.key,h='<div class=flag id=s560fix'+(k=='credit_note'?' style=\"background:#eef4fb;border-color:#c8d9ee\"':'')+'><b>'+esc(j.fix.text)+'</b><br>';\n"
  " if(k=='blank'){h+='<button type=button class=b data-fix=restore>Restore</button> <button type=button class=b data-fix=keep>Leave it set aside</button>';}\n"
  " else if(k=='receipt'||k=='statement'||k=='credit_note'){h+='<button type=button class=b data-s560k=\"'+k+'\">Make it a '+({receipt:'Receipt',statement:'Statement',credit_note:'Credit note'}[k])+'</button> <button type=button class=b data-fix=keep>No — leave it</button>';}\n", what="E35 fixb")
e("$('readbox').addEventListener('toggle',function(){S.readopen=$('readbox').open;cue();});\n",
  BLOCK_JS + "$('readbox').addEventListener('toggle',function(){S.readopen=$('readbox').open;cue();});\n", what="E36 the S835 script")
e('\n\n# ---------------------------------------------------------------------------------------------- the mount\ndef init(ar):\n',
  BLOCK_PY.rstrip("\n") + '\n\n\n# ---------------------------------------------------------------------------------------------- the mount\ndef init(ar):\n', what="E37 the S835 block")

e('            ("desk.yuvika", "Yuvika slips on the desk"))                                # S739 (absent = OFF)\n',
  '            ("desk.yuvika", "Yuvika slips on the desk"),                                # S739 (absent = OFF)\n'
  '            ("desk.cn", "Credit notes on the desk"))                                    # S835 (absent = OFF; the owner sees it always)\n', what="E38 SWITCHES")
e('            "desk.yuvika": _s739_on(db)}                                                              # S739\n',
  '            "desk.yuvika": _s739_on(db),                                                              # S739\n'
  '            "desk.cn": (_setting(db, "desk.cn", "off") or "").strip().lower() == "on"}               # S835\n', what="E39 switch_states")
e('"save": url_for("s551_api_save"), "groups": groups, "kinds": [list(k) for k in KINDS], ',
  '"save": url_for("s551_api_save"), "groups": groups, "kinds": [list(k) for k in KINDS if k[0] != "credit_note" or _s835_on(db, owner)], ', what="E40 desk_page kinds")
e('    hints, dest, dest_line = [], "", ""\n    yuv = _yuvika(b["vendor"])\n',
  '    if kind == "credit_note" and kind_from != "paper" and not _s835_on(db, owner):      # S835: not offered while desk.cn is off\n'
  '        kind, kind_from = "", ""\n'
  '    hints, dest, dest_line = [], "", ""\n    yuv = _yuvika(b["vendor"])\n', what="E41 paper_json kind while off")

e('        if dest == "clinic_equipment" and b["kind"] != "Asset":\n',
  '        if dest == "clinic_equipment" and b["kind"] != "Asset" and not s835.get("cn"):      # S835: a credit note is no asset purchase\n', what="E42 clinic_equipment kind")
e('        if dest == "clinic_equipment" and not owner and b["status"] == "draft":\n',
  '        if dest == "clinic_equipment" and not owner and b["status"] == "draft" and not s835.get("cn"):\n', what="E43 clinic_equipment line")
e("s715gate(ok);s739gate();}", "s715gate(ok);s739gate();s835gate();}", what="E44 paint2: s835gate last")
out = {"sorting_desk.py": t}
n_sd = len(E)

# ------------------------------------------------------------------ clinic_papers.py
c = src["clinic_papers.py"]
c = ed(c, '    return w + _tail(db, alias, ("challan", "receipt", "statement"))      # S531; S560: nor a receipt / statement\n',
       '    return w + _tail(db, alias, ("challan", "receipt", "statement", "credit_note"))      # S531; S560: nor a receipt / statement; S835 nor a credit note\n', 2, "C1 _live, _live_sections")
c = ed(c, '    if "doc_kind" in b.keys() and (b["doc_kind"] or "") in ("receipt", "statement"):\n',
       '    if "doc_kind" in b.keys() and (b["doc_kind"] or "") in ("receipt", "statement", "credit_note"):      # S835: nor a credit note\n', 1, "C2 _accept")
c = ed(c, '''                          "AND COALESCE(b.doc_kind,'bill') NOT IN ('receipt','statement') ORDER BY b.id").fetchall()      # S560\n''',
       '''                          "AND COALESCE(b.doc_kind,'bill') NOT IN ('receipt','statement','credit_note') ORDER BY b.id").fetchall()      # S560; S835\n''', 1, "C3 heal")
c = ed(c, '''or (b["doc_kind"] or "") in ("challan", "receipt", "statement"):      # S560\n''',
       '''or (b["doc_kind"] or "") in ("challan", "receipt", "statement", "credit_note"):      # S560; S835\n''', 1, "C4 challan_for_bill")
out["clinic_papers.py"] = c

# ------------------------------------------------------------------ xray_costs.py
x = src["xray_costs.py"]
x = ed(x, '            v.films_month_total = float(sd._s566_total(paid))\n',
       '            v.films_month_total = float(sd._s566_total(paid + (list(sd._s835_cn_rows(db, key, subs, ym)) if hasattr(sd, "_s835_cn_rows") else [])))      # S835: less the credit notes, as The month\n',
       1, "X1 films total")
out["xray_costs.py"] = x

# ------------------------------------------------------------------ claude_reader.py (appended block; nothing above it changes)
r = src["claude_reader.py"]
r = r.rstrip("\n") + "\n" + rd(os.path.join(BLK, "block_reader.py")).decode("utf-8")
out["claude_reader.py"] = r

os.makedirs(OUT, exist_ok=True)
for f, txt in out.items():
    with open(os.path.join(OUT, f), "wb") as fh:
        fh.write(txt.encode("utf-8"))
    print("%-18s %s" % (f, hashlib.md5(txt.encode("utf-8")).hexdigest()))
print("edits: sorting_desk %d (E01-E44) · clinic_papers 4 anchors / 5 places · xray_costs 1 · claude_reader 1 appended block" % n_sd)
