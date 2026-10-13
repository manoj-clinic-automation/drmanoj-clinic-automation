#!/usr/bin/env python3
"""S544_RECEPTION_FIVE (D719 kit a; F-891) -- exact, counted edits on the md5-pinned live asset_register.py and clinic_papers.py.
usage: make_s544.py <dir with the live files> <out dir>
Refuses unless both inputs are the pinned bytes and every anchor occurs exactly once."""
import hashlib, os, sys

FROM = {"asset_register.py": "35f9e823b07830b5831efc586f48d46b", "clinic_papers.py": "476e157c82f17a0af164019b04ccbb2b"}
src_d, out_d = sys.argv[1], sys.argv[2]

AR_EDITS = [
    ("A1 the asset category renamed (D719)",
     'CATEGORIES = ["Lab Equipment", "Medical Equipment", ',
     'CATEGORIES = ["Lab Equipment", "Dr MK Clinic Equipment", '),
    ("A2 the column: whose personal expense",
     '        ("challan_of",    "ALTER TABLE bills ADD COLUMN challan_of INTEGER"),      # S531: the bill it was joined to\n',
     '        ("challan_of",    "ALTER TABLE bills ADD COLUMN challan_of INTEGER"),      # S531: the bill it was joined to\n'
     '        ("pe_who",        "ALTER TABLE bills ADD COLUMN pe_who TEXT"),             # S544 (D719): a personal expense\'s person; NULL = Dr MK\n'),
    ("A3 the rows already in Medical Equipment move with it (idempotent, every start)",
     "\"WHEN kind='Expense' THEN 'owner_expense' WHEN kind='Document' THEN 'other_doc' ELSE 'clinic' END WHERE lane IS NULL\")\n",
     "\"WHEN kind='Expense' THEN 'owner_expense' WHEN kind='Document' THEN 'other_doc' ELSE 'clinic' END WHERE lane IS NULL\")\n"
     "    db.execute(\"UPDATE assets SET category='Dr MK Clinic Equipment' WHERE category='Medical Equipment'\")   # S544 (D719): renamed, nothing left behind\n"),
    ("A4 the lane's words",
     '    "owner_expense": ("Dr MK expense", "Expense", "captured"),\n',
     '    "owner_expense": ("Personal expense", "Expense", "captured"),           # S544 (D719): was "Dr MK expense"; Dr MK / Dr Bhawna in bills.pe_who\n'),
    ("A6 the reception lanes, their words, the switch",
     'def _intake_prefill():\n',
     '# S544 (D719): reception captures only -- four lanes and the challan tap; the owner and the managers keep Personal expense.\n'
     'RECEPTION_LANES_S544 = ("clinic", "pharmacy", "lab_purchase", "other_doc")\n'
     'LANE_WORDS_S544 = {"clinic": ("Clinic", "clinic ka saamaan, machine, service"),\n'
     '                   "pharmacy": ("Pharmacy", "Sanjeevni \\u2014 dawai ka bill"),\n'
     '                   "lab_purchase": ("NK Pathology", "lab ka purchase"),\n'
     '                   "other_doc": ("Other document", "bill nahi \\u2014 chitthi, form, resume"),\n'
     '                   "owner_expense": ("Personal expense", "Dr MK / Dr Bhawna")}\n'
     '\n'
     '\n'
     'def _lanes5_on():\n'
     '    """S544: the lane buttons on the intake -- the owner\'s switch on /admin (settings scan.lanes5), installed OFF."""\n'
     '    try:\n'
     '        return (setting_or("scan.lanes5", "off") or "").strip().lower() == "on"\n'
     '    except Exception:                                                # noqa: BLE001\n'
     '        return False\n'
     '\n'
     '\n'
     'def _intake_lanes_s544(role):\n'
     '    return RECEPTION_LANES_S544 + (("owner_expense",) if role in ("owner", "manager") else ())\n'
     '\n'
     '\n'
     'def _private_s544(b):\n'
     '    """S544 (F-891): a paper in the section Personal is the owner\'s alone -- on the bill doors as on the papers page."""\n'
     '    try:\n'
     '        sg = b["subgroup"]\n'
     '    except (IndexError, KeyError):\n'
     '        sg = None\n'
     '    return (sg or "") == "personal" and g.user["role"] != "owner"\n'
     '\n'
     '\n'
     'def _intake_prefill():\n'),
    ("A7 the intake: the lanes this login may choose",
     '    _lane_default = _lane_for_user(db, g.user["username"])      # S409: each person\'s drop-down opens on their own head\n'
     '    scan_cfg["uploadFields"].setdefault("lane", _lane_default)\n',
     '    _lane_default = _lane_for_user(db, g.user["username"])      # S409: each person\'s drop-down opens on their own head\n'
     '    _l5 = _lanes5_on()                                          # S544 (D719): reception captures only -- the lane buttons\n'
     '    _l5_keys = _intake_lanes_s544(g.user["role"]) if _l5 else ()\n'
     '    if _l5 and (_lane_default not in _l5_keys or _lane_default == "owner_expense"):    # nobody opens on the expense lane\n'
     '        _lane_default = "clinic"\n'
     '    if _l5 and scan_cfg["uploadFields"].get("lane") is not None and scan_cfg["uploadFields"]["lane"] not in _l5_keys:\n'
     '        scan_cfg["uploadFields"].pop("lane", None)\n'
     '    scan_cfg["uploadFields"].setdefault("lane", _lane_default)\n'),
    ("A8 the intake: the buttons above the lane line",
     '<div class=card style="padding:12px 14px;order:1">\n<div style="font-size:17px;font-weight:700"><span id=lane_line>',
     '<div class=card style="padding:12px 14px;order:1">\n'
     '{% if l5 %}<div style="font-size:15px;font-weight:700;margin:0 0 8px">{{\'Whose paper is this?\' if l5_owner else \'Yeh kaagaz kiska hai?\'}}</div>\n'
     '<div id=l5grid style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin:0 0 10px">{% for k in l5_keys %}{% if k!=\'owner_expense\' %}'
     '<button type=button class=l5b data-lane="{{k}}" style="min-height:70px;text-align:left;padding:8px 12px;border-radius:10px;border:2px solid #c9d2dc;background:#fff;color:#1f2a36;font-family:inherit;cursor:pointer">'
     '<span style="display:block;font-size:17px;font-weight:700">{{l5_words[k][0]}}</span>{% if not l5_owner %}<span style="display:block;font-size:12px;font-weight:400;color:#4a5866;margin-top:3px">{{l5_words[k][1]}}</span>{% endif %}</button>{% endif %}{% endfor %}</div>\n'
     '{% if \'owner_expense\' in l5_keys %}<button type=button class=l5b data-lane=owner_expense style="display:block;width:100%;min-height:58px;text-align:left;padding:8px 12px;border-radius:10px;border:2px solid #c9d2dc;background:#fff;color:#1f2a36;font-family:inherit;cursor:pointer;margin:0 0 10px">'
     '<span style="display:block;font-size:17px;font-weight:700">Personal expense</span><span style="display:block;font-size:12px;font-weight:400;color:#4a5866;margin-top:3px">{{\'only you and Shavez see this button\' if l5_owner else \'sirf Dr MK aur aap ko dikhta hai\'}}</span></button>\n'
     '<div id=l5who style="display:none;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin:0 0 6px">'
     '<button type=button class=l5w data-who=mk style="min-height:48px;border-radius:10px;border:2px solid #c9d2dc;background:#fff;color:#1f2a36;font-size:16px;font-weight:700;font-family:inherit;cursor:pointer">Dr MK</button>'
     '<button type=button class=l5w data-who=bhawna style="min-height:48px;border-radius:10px;border:2px solid #c9d2dc;background:#fff;color:#1f2a36;font-size:16px;font-weight:700;font-family:inherit;cursor:pointer">Dr Bhawna</button></div>\n'
     '<p id=l5whohint class=muted style="display:none;margin:0 0 8px;font-size:12px">{{\'Nothing chosen = Dr MK.\' if l5_owner else \'Kuch na chuno to Dr MK.\'}}</p>{% endif %}{% endif %}\n'
     '<div style="font-size:17px;font-weight:700"><span id=lane_line>'),
    ("A9 the intake: the link opens the month (the lane is on the buttons)",
     'return false">—&nbsp;badlo</a>',
     'return false">{% if l5 %}— mahina badlo{% else %}—&nbsp;badlo{% endif %}</a>'),
    ("A10 the lane line names the person of a personal expense",
     "l.textContent=s.options[s.selectedIndex].text.split(' — ')[0]+' · '",
     "var _b5=document.querySelector('.l5b[data-lane=\"'+s.value+'\"] span');l.textContent=(_b5?_b5.textContent:s.options[s.selectedIndex].text.split(' — ')[0])+((s.value==='owner_expense')?(' · '+((((window.SCANNER_CONFIG||{}).uploadFields||{}).pe_who==='bhawna')?'Dr Bhawna':'Dr MK')):'')+' · '"),
    ("A11 the old drop-down hidden when the buttons show, and holding only this login's lanes",
     '<label for=intake_lane style="margin-top:0">What kind of bill is this?</label>\n<select id=intake_lane style="max-width:300px"',
     '<label for=intake_lane style="margin-top:0{{\';display:none\' if l5}}">What kind of bill is this?</label>\n<select id=intake_lane style="max-width:300px{{\';display:none\' if l5}}"'),
    ("A12 the drop-down's options",
     "{% for k in lane_order %}<option value=\"{{k}}\" {{'selected' if k==lane_default}}>{{lanes[k][0]}}</option>{% endfor %}",
     "{% for k in (l5_keys if l5 else lane_order) %}<option value=\"{{k}}\" {{'selected' if k==lane_default}}>{{lanes[k][0]}}</option>{% endfor %}"),
    ("A13 the basic upload carries whose expense",
     '<input type=hidden name=challan id=challan_basic value="">',
     '<input type=hidden name=challan id=challan_basic value=""><input type=hidden name=pe_who id=pe_basic value="">'),
    ("A14 the buttons' script, and the first paint",
     "_laneLine();})();</script>\n{{today_html}}{{who_js}}",
     "_laneLine();if(window._l5Paint){window._l5Paint();}})();</script>\n"
     "{% if l5 %}<script>(function(){function sty(b,on,col){b.style.border=on?('3px solid '+(col||'#2b5d8a')):'2px solid #c9d2dc';b.style.background=on?(col?'#efe7f6':'#e3edf7'):'#fff';}\n"
     "window._l5Paint=function(){var s=document.getElementById('intake_lane');var v=s?s.value:'';\n"
     "document.querySelectorAll('.l5b').forEach(function(b){var pe=b.getAttribute('data-lane')==='owner_expense';sty(b,b.getAttribute('data-lane')===v,pe?'#6b4a8a':null);});\n"
     "var w=document.getElementById('l5who'),h=document.getElementById('l5whohint');if(w){w.style.display=(v==='owner_expense')?'grid':'none';}if(h){h.style.display=(v==='owner_expense')?'block':'none';}\n"
     "var who=(((window.SCANNER_CONFIG||{}).uploadFields||{}).pe_who)||'mk';document.querySelectorAll('.l5w').forEach(function(b){sty(b,b.getAttribute('data-who')===who);});};\n"
     "document.querySelectorAll('.l5b').forEach(function(b){b.addEventListener('click',function(){var s=document.getElementById('intake_lane');if(!s){return;}s.value=b.getAttribute('data-lane');if(s.onchange){s.onchange();}window._l5Paint();});});\n"
     "document.querySelectorAll('.l5w').forEach(function(b){b.addEventListener('click',function(){var v=b.getAttribute('data-who');if(window.SCANNER_CONFIG){window.SCANNER_CONFIG.uploadFields.pe_who=v;}var hb=document.getElementById('pe_basic');if(hb){hb.value=v;}window._l5Paint();_laneLine();});});\n"
     "window._l5Paint();})();</script>{% endif %}\n"
     "{{today_html}}{{who_js}}"),
    ("A15 the intake's render arguments",
     "scan_cfg=scan_cfg, widget_url=widget_url, lanes=LANES, lane_order=LANE_ORDER, lane_default=_lane_default,",
     "scan_cfg=scan_cfg, widget_url=widget_url, lanes=LANES, lane_order=LANE_ORDER, lane_default=_lane_default,\n"
     "        l5=_l5, l5_keys=_l5_keys, l5_owner=(g.user[\"role\"] == \"owner\"), l5_words=LANE_WORDS_S544,                # S544"),
    ("A16 the server keeps reception to its lanes when the buttons are on",
     "    _lane = _lane_key(lane)                                  # S409 (D625): five lanes; an unknown value is the clinic lane, as before\n",
     "    _lane = _lane_key(lane)                                  # S409 (D625): five lanes; an unknown value is the clinic lane, as before\n"
     "    if _lanes5_on() and _lane not in _intake_lanes_s544(g.user[\"role\"]):     # S544 (D719): reception captures only\n"
     "        _lane = \"clinic\"\n"),
    ("A17 whose personal expense, from the intake",
     "    bid = cur.lastrowid\n    if challan:",
     "    bid = cur.lastrowid\n"
     "    if _lane == \"owner_expense\" and (request.form.get(\"pe_who\") or \"\").strip().lower() == \"bhawna\":   # S544: none = Dr MK\n"
     "        db.execute(\"UPDATE bills SET pe_who='bhawna' WHERE id=?\", (bid,))\n"
     "    if challan:"),
    ("A18 the admin switch: the action",
     '        elif act == "set_palette":\n',
     '        elif act == "set_scan_lanes5":                                                 # S544 (D719)\n'
     '            db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(\'scan.lanes5\',?)",\n'
     '                       ("on" if request.form.get("on") == "1" else "off",))\n'
     '            flash("Reception\'s lane buttons on the bill intake are now %s." % ("ON" if request.form.get("on") == "1" else "OFF"))\n'
     '        elif act == "set_palette":\n'),
    ("A19 the admin switch: the card",
     "<button class=\"btn small\">{{'Switch OFF' if scan_cv else 'Switch ON'}}</button></form></div>\n",
     "<button class=\"btn small\">{{'Switch OFF' if scan_cv else 'Switch ON'}}</button></form></div>\n"
     "<div class=card><h4>Bill intake \\u2014 reception's lane buttons</h4>\n"
     "<p class=muted>When ON, reception sees four big buttons (Clinic \\u00b7 Pharmacy \\u00b7 NK Pathology \\u00b7 Other document) and the Challan button; "
     "Personal expense is offered to you and Shavez only, with Dr MK / Dr Bhawna. When OFF, the intake is as before.</p>\n"
     "<p>Now: <b>{{'ON' if lanes5 else 'OFF'}}</b></p>\n"
     "<form method=post><input type=hidden name=action value=set_scan_lanes5><input type=hidden name=on value=\"{{'0' if lanes5 else '1'}}\">\n"
     "<button class=\"btn small\">{{'Switch OFF' if lanes5 else 'Switch ON'}}</button></form></div>\n"),
    ("A20 the admin switch: its reading",
     "scan_cv=_scan_cv_on(), opencv_present=os.path.exists(OPENCV_JS_PATH),",
     "scan_cv=_scan_cv_on(), opencv_present=os.path.exists(OPENCV_JS_PATH), lanes5=_lanes5_on(),          # S544"),
    ("A21 F-891: the thumbnail door",
     '    b = get_db().execute("SELECT id, kind, lane, status, submitted_by, source_stored FROM bills WHERE id=?", (bid,)).fetchone()\n'
     '    if not b or not b["source_stored"]:\n'
     '        abort(404)\n'
     '    if not _staff_may_see(b, image=True):\n'
     '        abort(403)\n',
     '    b = get_db().execute("SELECT * FROM bills WHERE id=?", (bid,)).fetchone()\n'
     '    if not b or not b["source_stored"]:\n'
     '        abort(404)\n'
     '    if not _staff_may_see(b, image=True) or _private_s544(b):   # S544 (F-891)\n'
     '        abort(403)\n'),
    ("A22 F-891: the file door",
     '    b = get_db().execute("SELECT source_stored, source_orig, kind, lane, status, submitted_by FROM bills WHERE id=?", (bid,)).fetchone()\n'
     '    if not b or not b["source_stored"]:\n'
     '        abort(404)\n'
     '    if not _staff_may_see(b, image=True):',
     '    b = get_db().execute("SELECT * FROM bills WHERE id=?", (bid,)).fetchone()\n'
     '    if not b or not b["source_stored"]:\n'
     '        abort(404)\n'
     '    if _private_s544(b):                                         # S544 (F-891)\n'
     '        abort(403)\n'
     '    if not _staff_may_see(b, image=True):'),
    ("A23 F-891: the bill page",
     '                   "LEFT JOIN users u ON u.id=b.created_by WHERE b.id=?", (bid,)).fetchone()\n'
     '    if not b:\n'
     '        abort(404)\n'
     '    items = db.execute("SELECT * FROM bill_items WHERE bill_id=? ORDER BY id", (bid,)).fetchall()\n',
     '                   "LEFT JOIN users u ON u.id=b.created_by WHERE b.id=?", (bid,)).fetchone()\n'
     '    if not b:\n'
     '        abort(404)\n'
     '    if _private_s544(b):                                         # S544 (F-891)\n'
     '        abort(403)\n'
     '    items = db.execute("SELECT * FROM bill_items WHERE bill_id=? ORDER BY id", (bid,)).fetchall()\n'),
    ("A25 F-891: every checker door that looks a bill up (edit, approve, reread, reject, month, lane, dup)",
     'def _bill_or_404(bid):\n'
     '    b = get_db().execute("SELECT b.*, u.display_name entered_by FROM bills b "\n'
     '                         "LEFT JOIN users u ON u.id=b.created_by WHERE b.id=?", (bid,)).fetchone()\n'
     '    if not b:\n'
     '        abort(404)\n'
     '    return b\n',
     'def _bill_or_404(bid):\n'
     '    b = get_db().execute("SELECT b.*, u.display_name entered_by FROM bills b "\n'
     '                         "LEFT JOIN users u ON u.id=b.created_by WHERE b.id=?", (bid,)).fetchone()\n'
     '    if not b:\n'
     '        abort(404)\n'
     '    if _private_s544(b):                                         # S544 (F-891)\n'
     '        abort(403)\n'
     '    return b\n'),
    ("A26 F-891: a supplier's purchase history",
     "\"WHERE vendor=? AND status='approved' ORDER BY bill_date DESC, id DESC LIMIT 40\",",
     "\"WHERE vendor=? AND status='approved'\" + (\"\" if is_owner() else \" AND COALESCE(subgroup,'')<>'personal'\") +   # S544 (F-891)\n"
     "                       \" ORDER BY bill_date DESC, id DESC LIMIT 40\","),
    ("A24 F-891: the bills list",
     '    where, params = "1=1", []\n',
     '    where, params = "1=1", []\n'
     '    if not is_owner():                                            # S544 (F-891): a Personal paper is the owner\'s alone\n'
     '        where += " AND COALESCE(b.subgroup,\'\')<>\'personal\'"\n'),
]

CP_EDITS = [
    ("C1 version", 'VERSION = "S532.1"', 'VERSION = "S544.1"'),
    ("C2 the suggestion's words",
     'return dict(kind="lane", value="owner_expense", label="Dr MK expense",',
     'return dict(kind="lane", value="owner_expense", label="Personal expense",'),
    ("C3 the stand's footnote",
     "lab and Dr MK expense scans go into the accountants' pack.",
     "lab scans and personal expenses go into the accountants' pack."),
    ("C4 the Personal expenses fold on the papers page",
     "{% for p in papers %}<div class=d6card>",
     "{% if pe %}<details class=\"d6x d6card\" style=\"padding:10px 14px\"><summary class=d6opt style=\"margin:0;border:0;padding:4px 36px 4px 0\">Personal expenses"
     "<small>Dr MK {{pe.mk_n}} · Dr Bhawna {{pe.bh_n}} — you and Shavez only</small></summary>\n"
     "{% for lab, rows in (('Dr MK', pe.mk), ('Dr Bhawna', pe.bh)) %}<div style=\"margin:10px 0 4px;font-weight:700;color:#3a5a78\">{{lab}}</div>\n"
     "{% if rows %}<table class=d6t>{% for r in rows %}<tr><td><a href=\"{{url_for('d664_paper',bid=r.id)}}\" style=\"text-decoration:none\"><b>{{r.stamp}}</b></a> · {{r.vendor or 'supplier not read'}}"
     "<br><span class=muted style=\"font-size:13px\">{{r.warr}}</span></td><td class=r>{{inr(r.amt) if r.amt is not none else ''}}</td></tr>{% endfor %}</table>"
     "{% else %}<p class=muted style=\"margin:0\">None yet.</p>{% endif %}{% endfor %}\n"
     "<p class=muted style=\"font-size:13px;margin:8px 0 2px\">A paper with no name chosen counts under Dr MK. Open a paper to set whose it is, its warranty, or to move it.</p></details>{% endif %}\n"
     "{% for p in papers %}<div class=d6card>"),
    ("C5 the paper page: no section here",
     "Sections belong to papers on the Clinic, Other-document and Dr MK expense lanes;",
     "Sections belong to papers on the Clinic, Other-document and Personal expense lanes;"),
    ("C6 the paper page: whose expense",
     '{% if on_expense %}<div class=d6card><b style="font-size:16px">Keep the warranty</b>',
     '{% if on_expense %}<div class=d6card><b style="font-size:16px">Personal expense — whose?</b>\n'
     '<form method=post action="{{url_for(\'d664_pe_who\',bid=p.b[\'id\'])}}" class=d6btns style="display:flex;margin-top:10px"><input type=hidden name=back value="{{back}}">\n'
     '<button class="d6b {{\'yes\' if pe_who!=\'bhawna\' else \'alt\'}}" name=who value=mk>Dr MK</button>\n'
     '<button class="d6b {{\'yes\' if pe_who==\'bhawna\' else \'alt\'}}" name=who value=bhawna>Dr Bhawna</button></form>\n'
     '<p class=muted style="font-size:13px;margin:8px 0 0">Nothing chosen counts as Dr MK.</p></div>{% endif %}\n'
     '{% if on_expense %}<div class=d6card><b style="font-size:16px">Keep the warranty</b>'),
    ("C7 the paper page: the warranty's footnote",
     "to you only. Dr MK expense is your own lane: it is kept apart",
     "to you only. A personal expense is shown to you and Shavez only: it is kept apart"),
    ("C8 the paper page's render arguments",
     "on_expense=_on_expense(b), w=w,",
     "on_expense=_on_expense(b), pe_who=_pe_who(b), w=w,"),
    ("C9 the stand: the row",
     '        rows.append(dict(name="Dr MK expense", n=me, text="to the accountants\' pack (8.2); %d with a warranty noted" % mw, href=None))\n',
     '        mb = n("SELECT COUNT(*) " + base + " AND b.lane=\'owner_expense\' AND COALESCE(b.pe_who,\'\')=\'bhawna\'") if "pe_who" in _cols(db) else 0\n'
     '        rows.append(dict(name="Personal expenses", n=me, text="Dr MK %d \\u00b7 Dr Bhawna %d; to the accountants\' pack (8.2); %d with a warranty noted" % (me - mb, mb, mw), href=None))   # S544\n'),
    ("C10 the month page's name for the lane",
     '"owner_expense": "Dr MK expense",',
     '"owner_expense": "Personal expenses",'),
    ("C11 the Renewals card's title",
     '<h3 style="color:#1f3864">Dr MK expense — warranties',
     '<h3 style="color:#1f3864">Personal expenses — warranties'),
    ("C12 the warranty refusal's words",
     '"%s is not on the Dr MK expense lane, so no warranty is kept for it. Move it there first." % stamp',
     '"%s is not a personal expense, so no warranty is kept for it. Move it there first." % stamp'),
    ("C13 the papers page's render arguments",
     "nch=challans_count(db),\n                   flow=AR._flow(\"Papers to sort\", url_for(\"bills_list\")))",
     "nch=challans_count(db), pe=personal_expenses(db),                                       # S544\n"
     "                   flow=AR._flow(\"Papers to sort\", url_for(\"bills_list\")))"),
    ("C14 the functions: whose, the list, the door",
     "def init(ar):\n",
     "# ---------------------------------------------------------------------------------------------- S544: Personal expenses\n"
     "def _pe_who(b):\n"
     "    try:\n"
     "        return (b[\"pe_who\"] or \"\")\n"
     "    except (IndexError, KeyError):\n"
     "        return \"\"\n"
     "\n"
     "\n"
     "def personal_expenses(db):\n"
     "    \"\"\"S544 (D719): the live personal expenses, Dr MK's and Dr Bhawna's, newest first (50 each). None when there are none.\"\"\"\n"
     "    try:\n"
     "        has = \"pe_who\" in _cols(db)\n"
     "        w = (\"COALESCE(b.lane,'clinic')='owner_expense' AND b.status<>'rejected' AND b.dup_of IS NULL\"\n"
     "             + (\" AND b.page_of IS NULL\" if \"page_of\" in _cols(db) else \"\"))\n"
     "        if not AR.is_owner():                                        # F-891: a Personal paper is the owner's alone\n"
     "            w += \" AND COALESCE(b.subgroup,'')<>'personal'\"\n"
     "        out = {\"mk\": [], \"bh\": []}\n"
     "        nt = db.execute(\"SELECT COUNT(*) FROM bills b WHERE \" + w).fetchone()[0]\n"
     "        nb = db.execute(\"SELECT COUNT(*) FROM bills b WHERE \" + w + \" AND COALESCE(b.pe_who,'')='bhawna'\").fetchone()[0] if has else 0\n"
     "        out[\"mk_n\"], out[\"bh_n\"] = nt - nb, nb\n"
     "        for b in db.execute(\"SELECT b.* FROM bills b WHERE \" + w + \" ORDER BY b.id DESC LIMIT 200\"):\n"
     "            k = \"bh\" if (has and (b[\"pe_who\"] or \"\") == \"bhawna\") else \"mk\"\n"
     "            if len(out[k]) >= 50:\n"
     "                continue\n"
     "            wl = warranty_label(b) if _on_expense(b) else \"\"\n"
     "            out[k].append(dict(id=b[\"id\"], stamp=_stamp(b), vendor=b[\"vendor\"], amt=b[\"total_amount\"],\n"
     "                               warr=(wl or \"no warranty noted\")))\n"
     "        return out if nt else None\n"
     "    except Exception:                                                # noqa: BLE001\n"
     "        return None\n"
     "\n"
     "\n"
     "def set_pe_who(bid):\n"
     "    \"\"\"S544: Dr MK or Dr Bhawna, on a personal expense. The owner and the managers (the papers page's own door).\"\"\"\n"
     "    db = AR.get_db()\n"
     "    b = db.execute(\"SELECT * FROM bills WHERE id=?\", (bid,)).fetchone()\n"
     "    if not b:\n"
     "        abort(404)\n"
     "    if (b[\"subgroup\"] or \"\") == \"personal\" and not AR.is_owner():\n"
     "        abort(403)                                                   # F-891: a Personal paper is the owner's alone\n"
     "    if not _on_expense(b):\n"
     "        flash(\"%s is not a personal expense.\" % _stamp(b))\n"
     "        return redirect(_back())\n"
     "    who = (request.form.get(\"who\") or \"\").strip().lower()\n"
     "    val = \"bhawna\" if who == \"bhawna\" else None\n"
     "    db.execute(\"UPDATE bills SET pe_who=? WHERE id=?\", (val, bid))\n"
     "    AR._audit_bill(db, bid, \"pe_who\", {\"to\": val or \"mk\"})\n"
     "    db.commit()\n"
     "    flash(\"%s: Dr %s's expense.\" % (_stamp(b), \"Bhawna\" if val else \"MK\"))\n"
     "    return redirect(_back())\n"
     "\n"
     "\n"
     "def init(ar):\n"),
    ("C15 the door's address",
     '    app.add_url_rule("/papers/<int:bid>/warranty", "d664_warranty", ar.checker_required(set_warranty), methods=["POST"])\n',
     '    app.add_url_rule("/papers/<int:bid>/warranty", "d664_warranty", ar.checker_required(set_warranty), methods=["POST"])\n'
     '    app.add_url_rule("/papers/<int:bid>/pe_who", "d664_pe_who", ar.checker_required(set_pe_who), methods=["POST"])            # S544\n'),
]


def apply(name, edits):
    raw = open(os.path.join(src_d, name), "rb").read()
    if hashlib.md5(raw).hexdigest() != FROM[name]:
        sys.exit("REFUSED: %s is not the pinned %s" % (name, FROM[name]))
    s = raw.decode("utf-8")
    for label, old, new in edits:
        n = s.count(old)
        if n != 1:
            sys.exit("REFUSED: %s %s -- anchor found %d times (must be 1)" % (name, label, n))
        s = s.replace(old, new, 1)
    b = s.encode("utf-8")
    open(os.path.join(out_d, name), "wb").write(b)
    print("%s: %d edits . %s" % (name, len(edits), hashlib.md5(b).hexdigest()))


os.makedirs(out_d, exist_ok=True)
apply("asset_register.py", AR_EDITS)
apply("clinic_papers.py", CP_EDITS)
