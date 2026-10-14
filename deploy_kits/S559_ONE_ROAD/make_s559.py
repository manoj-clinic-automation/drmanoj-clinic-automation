#!/usr/bin/env python3
"""make_s559.py -- S559_ONE_ROAD: the five edited files rebuilt from the pinned live bytes.

    python3 make_s559.py <dir with the live asset_register.py, sorting_desk.py, clinic_papers.py, asset_machine.py,
                          scanner_widget.js> <out dir>

Exact counted edits (BUILD_NORM_v1): refuses when an input is not at its FROM pin or an anchor is not found exactly the
counted number of times. Every byte of each built file comes from the live file plus these edits. No new file."""
import hashlib, os, sys

FROM = {"asset_register.py": "9e94b11c1a55eee6fdb22b9862b6db44",
        "sorting_desk.py": "91a04674e27de3fbfc7602403403c821",
        "clinic_papers.py": "058c9bcb5a4973f8a15984b645ff57d7",
        "asset_machine.py": "66c37197ae7c0d63874e213d52e7b9e5",
        "scanner_widget.js": "1143c77b13ae62652d4d961a92b9a9ab"}

HERE = os.path.dirname(os.path.abspath(__file__))
# The helpers appended to asset_register.py (AR10) -- the kit's own text, read here (never imported).
with open(os.path.join(HERE, "s559_ar_block.txt"), "rb") as _fh:
    BLOCK = _fh.read().decode("utf-8")
D = "\\u2014"            # the files carry these as the six characters \u2014 / \u2190 inside non-raw template strings
L = "\\u2190"

# ============================================================================================ asset_register.py
AR_EDITS = [
    # AR1 (item 1) -- the bar: the owner and a manager get THE one bar (_s559_bar); anyone else the old header, byte for byte
    ("{% if not (flow and user and user['role']=='reception') %}<header>",
     "{% if s559bar %}{{s559bar}}{% elif not (flow and user and user['role']=='reception') %}<header>", 1),
    ("                                  palette_bg=PALETTES[pal][1], flow=flow)\n",
     "                                  palette_bg=PALETTES[pal][1], flow=flow, s559bar=_s559_bar(u))      # S559 item 1\n", 1),
    # AR2 (item 2) -- the home page opens with the desk's card
    ('    return page("""<h2>Dashboard</h2>\n',
     '    return page("""{{s559home}}<h2>Dashboard</h2>\n', 1),
    ('""", due=due, counts=counts, month_spend=month_spend)\n',
     '""", due=due, counts=counts, month_spend=month_spend, s559home=_s559_home(g.user))      # S559 item 2\n', 1),
    # AR3 (item 9) -- the Assets page's Zone filter: one option per zone name ("Unassigned" once); it filters every zone of it
    ('    # changing entity resets a now-invalid zone selection\n    if f_zone and f_zone not in {z["id"] for z in zone_opts}:\n        f_zone = None\n',
     '    # changing entity resets a now-invalid zone selection\n'
     '    zone_opts, s559_zids, f_zone = _s559_zone_once(zone_opts, f_zone)      # S559 item 9: one option per name\n', 1),
    ('        fclauses.append("a.zone_id=?"); fparams.append(f_zone)\n',
     '        fclauses.append("a.zone_id IN (%s)" % ",".join("?" * len(s559_zids))); fparams.extend(s559_zids)      # S559 item 9\n', 1),
    # AR4 (item 9) -- Renewals: the Kind column (one helper decides it) and dd-mm-yyyy
    ("        SELECT e.label, e.due_date, e.threshold_days, a.id aid, a.name aname,\n",
     "        SELECT e.label, e.due_date, e.threshold_days, a.id aid, a.name aname, a.contract_type s559_ct,\n", 1),
    ("<table><tr><th>Asset</th><th>What</th><th>Due</th><th>Status</th></tr>",
     "<table><tr><th>Asset</th><th>Kind</th><th>What</th><th>Due</th><th>Status</th></tr>", 1),
    ("<td><a href=\"{{url_for('asset_view',aid=r['aid'])}}\">{{r['aname']}}</a></td>\n<td>{{r['label']}}</td><td>{{r['due_date']}}</td>",
     "<td><a href=\"{{url_for('asset_view',aid=r['aid'])}}\">{{r['aname']}}</a></td>\n<td>{{s559_kind(r['label'], r['s559_ct'])}}</td>"
     "<td>{{r['label']}}</td><td>{{r['due_date']|s559_dmy}}</td>", 1),
    ("<td>{{r['batch'] or '" + D + "'}}</td><td>{{r['expiry']}}</td>",
     "<td>{{r['batch'] or '" + D + "'}}</td><td>{{r['expiry']|s559_dmy}}</td>", 1),
    # AR5 (item 9) -- the machine page: dd-mm-yyyy, the purchase paper to the desk (item 4), the PM sentence only under a live AMC/CMC
    ("<b>Purchased:</b> {{a['purchase_date'] or '—'}}",
     "<b>Purchased:</b> {{a['purchase_date']|s559_dmy if a['purchase_date'] else '—'}}", 1),
    ("<b>From bill:</b> <a href=\"{{url_for('bill_view',bid=a['bill_id'])}}\">",
     "<b>From bill:</b> <a href=\"{{s559_href(a['bill_id'])}}\">", 1),
    ("<span class=muted>none set</span>{% endif %}\n{% for e,state,days in exp %}<div>{{e['label']}}: <b>{{e['due_date']}}</b>",
     "<span class=muted>none set</span>{% endif %}\n{% for e,state,days in exp %}<div>{{e['label']}}: <b>{{e['due_date']|s559_dmy}}</b>", 1),
    ("{% for p in parts %}<tr><td>{{p['part_replaced']}}</td><td>{{p['log_date']}}</td>\n<td>{{p['part_warranty'] or '" + D + "'}}</td>",
     "{% for p in parts %}<tr><td>{{p['part_replaced']}}</td><td>{{p['log_date']|s559_dmy}}</td>\n<td>{{p['part_warranty']|s559_dmy if p['part_warranty'] else '" + D + "'}}</td>", 1),
    ("<span class=muted>by {{f['up_by']}} {{f['uploaded_at'][:10]}}",
     "<span class=muted>by {{f['up_by']}} {{f['uploaded_at'][:10]|s559_dmy}}", 1),
    ("{% for s in logs %}<tr><td>{{s['log_date']}}</td>",
     "{% for s in logs %}<tr><td>{{s['log_date']|s559_dmy}}</td>", 1),
    ("<td>{{s['done_by'] or ''}}</td><td>{{s['next_due'] or ''}}</td>",
     "<td>{{s['done_by'] or ''}}</td><td>{{s['next_due']|s559_dmy if s['next_due'] else ''}}</td>", 1),
    ("<div class=muted id=pmnote>Preventive maintenance is covered under the AMC — no charge.</div>",
     "{% if s559pm %}<div class=muted id=pmnote>Preventive maintenance is covered under the AMC — no charge.</div>{% endif %}", 1),
    ("today=today().isoformat(), s557=_s557_machine(a))      # S557: the machine pages\n",
     "today=today().isoformat(), s557=_s557_machine(a), s559pm=_s559_pm(a))      # S557: the machine pages; S559 item 9\n", 1),
    # AR6 (items 1, 6, 7, 8, 9) -- All papers (the old "Purchases"): the title, the desk's one count, the true filter words,
    #                              one link to The month, every row to the desk, dd-mm-yyyy, BACK to the scan app's home
    ("""    return page(\"\"\"<h2>Purchases{% if npend %} <a href="{{url_for('bills_list',status='draft')}}" class="badge amber" style="text-decoration:none">{{npend}} pending</a>{% endif %}</h2>""",
     """    return page(\"\"\"<h2>All papers{% if s559n is not none %} <a href="{{url_for('s551_desk')}}" id=s559wait class="badge amber" style="text-decoration:none">{{s559n}} waiting on the desk →</a>{% elif npend %} <a href="{{url_for('bills_list',status='draft')}}" class="badge amber" style="text-decoration:none">{{npend}} pending</a>{% endif %}</h2>""", 1),
    ("<option {{'selected' if fs=='draft'}}>draft</option><option {{'selected' if fs=='approved'}}>approved</option><option {{'selected' if fs=='rejected'}}>rejected</option><option {{'selected' if fs=='captured'}}>captured</option>",
     "<option value=draft {{'selected' if fs=='draft'}}>Not accepted yet (draft)</option><option value=captured {{'selected' if fs=='captured'}}>Filed (captured)</option>"
     "<option value=approved {{'selected' if fs=='approved'}}>Accepted (approved)</option><option value=rejected {{'selected' if fs=='rejected'}}>Set aside (rejected)</option>", 1),
    ("{% if s551_month_href is defined %}<a class=\"btn small\" href=\"{{s551_month_href()}}\">The month</a>",
     "{% if s551_month_href is defined %}<a class=\"btn small\" href=\"{{url_for('s551_month')}}\">The month</a>", 1),
    ("{% if is_owner %}<a class=\"btn small\" href=\"{{url_for('s551_month') if s551_on is defined else url_for('purchases')}}\">\\U0001F4C8 {{'Consumption " + D + " now The month' if s551_on is defined else 'Consumption & rate history'}}</a> <a class=\"btn small\" href=\"{{url_for('lanes_admin')}}\">Scan lanes</a>{% endif %}</p>",
     "{% if is_owner %}{% if s551_on is not defined %}<a class=\"btn small\" href=\"{{url_for('purchases')}}\">\\U0001F4C8 Consumption & rate history</a> {% endif %}<a class=\"btn small\" href=\"{{url_for('lanes_admin')}}\">Scan lanes</a>{% endif %}</p>", 1),
    ("</td><td>{{b['bill_date'] or '" + D + "'}}</td>\n<td><a href=\"{{url_for('bill_view',bid=b['id'])}}\">{{b['vendor'] or '(no vendor)'}}</a></td>",
     "</td><td>{{b['bill_date']|s559_dmy if b['bill_date'] else '" + D + "'}}</td>\n<td><a href=\"{{s559_href(b)}}\">{{b['vendor'] or '(no vendor)'}}</a></td>", 1),
    ("{% else %}<a href=\"{{url_for('bill_view',bid=b['id'])}}\" title=\"open the paper to change its lane\">",
     "{% else %}<a href=\"{{s559_href(b)}}\" title=\"open the paper\">", 1),
    ("lane_order=LANE_ORDER, flow=_flow(\"Purchases\"), lane_word=_lane_word_s555,\n",
     "lane_order=LANE_ORDER, flow=_flow(\"All papers\", url_for(\"dashboard\")), lane_word=_lane_word_s555, s559n=_s559_desk_n(g.user),      # S559\n", 1),
    # AR7 (item 5) -- the old bill page: the badge tells the truth, the scan inline at the top, "Open on the sorting desk"
    ("{% if b['status']=='draft' %}<span class=\"badge amber\">PENDING</span>\n{% elif b['status']=='rejected' %}<span class=\"badge red\">REJECTED</span>\n{% else %}<span class=\"badge green\">approved</span>{% endif %}</h2>",
     "{% if b['status']=='draft' %}<span class=\"badge amber\" id=s559badge>Waiting</span>\n{% elif b['status']=='rejected' %}<span class=\"badge red\" id=s559badge>Set aside</span>\n"
     "{% elif b['status']=='captured' %}<span class=badge id=s559badge style=\"background:#5b6b7f;color:#fff\">Filed</span>\n"
     "{% elif b['status']=='approved' %}<span class=\"badge green\" id=s559badge>Accepted</span>\n{% else %}<span class=badge id=s559badge>{{b['status']}}</span>{% endif %}</h2>", 1),
    ("<p><a class=\"btn small\" href=\"{{url_for('bills_list')}}\">← Purchases</a>\n{% if b['ocr_status']=='reading' %}",
     "<p><a class=\"btn small\" href=\"{{url_for('bills_list')}}\">← All papers</a>\n"
     "{% if s559desk %}<a class=\"btn small\" id=s559desk href=\"{{s559desk}}\" style=\"background:#2b6e4f\">Open on the sorting desk</a>{% endif %}\n"
     "{% if b['ocr_status']=='reading' %}", 1),
    ("onsubmit=\"return confirm('Delete this bill and all its items?')\"><button class=\"btn small danger\">Delete</button></form>{% endif %}</p>\n<div class=grid>",
     "onsubmit=\"return confirm('Delete this bill and all its items?')\"><button class=\"btn small danger\">Delete</button></form>{% endif %}</p>\n"
     "{% if b['source_stored'] %}<div class=card id=s559scan style=\"padding:6px\"><iframe src=\"{{url_for('bill_file',bid=b['id'])}}\" title=\"the scan\" "
     "style=\"display:block;width:100%;height:70vh;border:0;border-radius:6px;background:#fbfaf7\"></iframe>"
     "<div style=\"margin:4px 2px 0\"><a href=\"{{url_for('bill_file',bid=b['id'])}}\" target=_blank>Open the file</a></div></div>{% endif %}\n"
     "<div class=grid>", 1),
    ("lanes=LANES, lane_order=LANE_ORDER, s557_line=_s557_paper_line(b),\n",
     "lanes=LANES, lane_order=LANE_ORDER, s557_line=_s557_paper_line(b), s559desk=_s559_desk_href(b),\n", 1),
    # AR8 (item 1) -- the page once called Purchases is "All papers" in its back links too
    (">← Purchases</a></p>", ">← All papers</a></p>", 1),
    (">" + L + " Purchases</a></p>", ">" + L + " All papers</a></p>", 2),
    # AR9 (item 1) -- Staff is out of the menu: reached from Admin (Drafts already is)
    ("<p class=muted>Drafts never expire and are never auto-deleted.</p></div>\"\"\",\n",
     "<p class=muted>Drafts never expire and are never auto-deleted.</p></div>\n"
     "<div class=card id=s559staff><h4>Staff</h4><p>Staff records and their documents. <a class=\"btn small\" href=\"{{url_for('staff_list')}}\">Open staff</a></p></div>\"\"\",\n", 1),
    # AR10 -- the helpers, after the machine pages' block
    ("# --- S557_MACHINE_PAGES end ---\n", "# --- S557_MACHINE_PAGES end ---\n" + BLOCK, 1),
]

# ============================================================================================ sorting_desk.py
SD_EDITS = [
    ("MACHINE = \"S557\"              # S557_MACHINE_PAGES: the machine-pages switch, one word per lane, a non-number amount ignored\n",
     "MACHINE = \"S557\"              # S557_MACHINE_PAGES: the machine-pages switch, one word per lane, a non-number amount ignored\n"
     "ROAD = \"S559\"                 # S559_ONE_ROAD: the one menu on the desk's pages, /desk?open=<id>, every paper row to the desk\n", 1),
    # SD1 (item 1) -- the one bar on the desk's four pages (and on the one-line page a manager sees while it is off)
    ("</head><body><div class=top><span class=t>Sorting desk</span></div>",
     "</head><body>{{s559_bar() if s559_bar is defined else ''}}<div class=top><span class=t>Sorting desk</span></div>", 1),
    ("</style></head><body><div id=app>\n<div class=top><span class=t>Sorting desk</span>",
     "</style></head><body><div id=app>\n{{s559_bar() if s559_bar is defined else ''}}<div class=top><span class=t>Sorting desk</span>", 1),
    ('PAGE_HEAD = HEAD + """</head><body>"""\n',
     'PAGE_HEAD = HEAD + """</head><body>{{s559_bar() if s559_bar is defined else \'\'}}"""      # S559 item 1: Bills awaited, the ledger, The month\n', 1),
    # SD2 (item 3) -- /desk?open=<id> (or ?open=B-0125): that paper in the middle and right panels, by the desk's own rules
    ("<span class=muted id=wt style=\"font-size:14px\">{{n}} paper{{'' if n==1 else 's'}} waiting · newest first</span>\n",
     "<span class=muted id=wt style=\"font-size:14px\">{{n}} paper{{'' if n==1 else 's'}} waiting · newest first</span>\n"
     "{% if cant %}<span id=s559cant style=\"font-size:13px;color:#6b7785\">That paper can't be opened here</span>{% endif %}\n", 1),
    ("loadList(0);\n})();\n</script></body></html>\"\"\"",
     "loadList(C.open||0);\n})();\n</script></body></html>\"\"\"", 1),
    ("    n = len(waiting(db, owner))\n    return render_template_string(DESK_TPL, bg=_bg(), cfg=cfg, n=n, owner=owner, chip=_chip(db), title=\"Sorting desk\")\n",
     "    n = len(waiting(db, owner))\n"
     "    cfg[\"open\"], cant = _s559_open(db, owner, request.args.get(\"open\"))      # S559 item 3\n"
     "    return render_template_string(DESK_TPL, bg=_bg(), cfg=cfg, n=n, owner=owner, chip=_chip(db), title=\"Sorting desk\", cant=cant)\n", 1),
    ("def api_list():\n",
     "def _s559_open(db, owner, v):\n"
     "    \"\"\"S559 item 3: (the paper's id, False) when /desk?open= names a paper this person may open on the desk -- by id, or by\n"
     "    its stamp (B-0125); (0, True) when it names one that is unknown or refused (never pharmacy; Personal only for the owner);\n"
     "    (0, False) when nothing is named. The same rule as picking it in the list (_visible).\"\"\"\n"
     "    v = re.sub(r\"\\s+\", \"\", str(v or \"\"))[:20]\n"
     "    if not v:\n"
     "        return 0, False\n"
     "    try:\n"
     "        b = _row(db, int(v)) if v.isdigit() else _by_stamp(db, v)\n"
     "    except (ValueError, OverflowError, sqlite3.Error):\n"
     "        b = None\n"
     "    if b is None or _visible(b, owner):\n"
     "        return 0, True\n"
     "    return b[\"id\"], False\n"
     "\n\n"
     "def api_list():\n", 1),
    # SD3 (item 4) -- every paper row on Bills awaited, the ledger and The month leads to the desk (s559_href: pharmacy keeps the old page)
    ("<b><a href=\"{{url_for('bill_view',bid=r.id)}}\" style=\"text-decoration:none;color:inherit\">{{r.stamp}}</a>",
     "<b><a href=\"{{s559_href(r.id) if s559_href is defined else url_for('bill_view',bid=r.id)}}\" style=\"text-decoration:none;color:inherit\">{{r.stamp}}</a>", 1),
    ("{% if r.bid %}<a href=\"{{url_for('bill_view',bid=r.bid)}}\">{{r.p}}</a>",
     "{% if r.bid %}<a href=\"{{s559_href(r.bid) if s559_href is defined else url_for('bill_view',bid=r.bid)}}\">{{r.p}}</a>", 1),
    ("<a href=\"{{url_for('bill_view',bid=e.bid)}}\">{{e.stamp}}</a> · {{e.vendor or 'supplier not read'}}",
     "<a href=\"{{s559_href(e.bid) if s559_href is defined else url_for('bill_view',bid=e.bid)}}\">{{e.stamp}}</a> · {{e.vendor or 'supplier not read'}}", 1),
]

# ============================================================================================ clinic_papers.py
CP_EDITS = [
    # CP1 (item 7) -- the papers list's toolbar: no link to the old month / challans pages while the desk is there
    (" &nbsp;<a href=\"{{url_for('d664_month')}}\">This month by group →</a> &nbsp;<a href=\"{{url_for('d664_challans')}}\">Bills awaited{% if nch %} ({{nch}}){% endif %} →</a></p>",
     "{% if s551_month_href is not defined %} &nbsp;<a href=\"{{url_for('d664_month')}}\">This month by group →</a> &nbsp;<a href=\"{{url_for('d664_challans')}}\">Bills awaited{% if nch %} ({{nch}}){% endif %} →</a>{% endif %}</p>", 1),
    ("&nbsp;<a href=\"{{s551_month_href()}}\">The month →</a>",
     "&nbsp;<a href=\"{{url_for('s551_month')}}\">The month →</a>", 1),
    # CP2 (item 4) -- each paper on the papers list (its picture, its stamp, its "Open it") leads to the desk
    ("<div class=d6row><a href=\"{{url_for('bill_view',bid=p.b['id'])}}\">{% if p.b['source_stored'] %}",
     "<div class=d6row><a href=\"{{s559_href(p.b) if s559_href is defined else url_for('bill_view',bid=p.b['id'])}}\">{% if p.b['source_stored'] %}", 1),
    ("<b><a href=\"{{url_for('bill_view',bid=p.b['id'])}}\" style=\"text-decoration:none\">{{p.stamp}}</a>",
     "<b><a href=\"{{s559_href(p.b) if s559_href is defined else url_for('bill_view',bid=p.b['id'])}}\" style=\"text-decoration:none\">{{p.stamp}}</a>", 1),
    ("<a class=\"d6b alt\" href=\"{{url_for('d664_paper',bid=p.b['id'])}}\">{{'Change' if (p.s and p.s.kind!='note') else 'Open it'}}</a>",
     # S559_FIX1 B1: to the desk only when this person's desk link IS a /desk link; else the papers page's own paper page
     #               (a manager while desk.on is off keeps /papers/<id>, where he sets the paper's place -- never the old bill page)
     "<a class=\"d6b alt\" href=\"{{s559_href(p.b) if (s559_href is defined and '/desk' in s559_href(p.b)) else url_for('d664_paper',bid=p.b['id'])}}\">{{'Change' if (p.s and p.s.kind!='note') else 'Open it'}}</a>", 1),
    # CP3 (item 7) -- in-app links to Bills awaited go to the desk's page
    ("text=\"goods received, bill not yet scanned\" if ch else \"none waiting\", href=url_for(\"d664_challans\")))",
     "text=\"goods received, bill not yet scanned\" if ch else \"none waiting\",\n"
     "                             href=url_for(\"s551_awaited\" if \"s551_awaited\" in AR.app.view_functions else \"d664_challans\")))      # S559 item 7", 1),
    ("It is on <a href=\"{{url_for('d664_challans')}}\">Bills awaited</a>;",
     "It is on <a href=\"{{url_for('s551_awaited') if s551_on is defined else url_for('d664_challans')}}\">Bills awaited</a>;", 1),
]

# ============================================================================================ asset_machine.py
AM_EDITS = [
    ("KINDS = ((\"warranty\", \"Warranty\"),",
     "ROAD = \"S559\"   # S559_ONE_ROAD: its paper leads to the desk; the old record's cover in the cover line; live_amc()\n"
     "KINDS = ((\"warranty\", \"Warranty\"),", 1),
    # AM1 (item 4) -- a machine page's "its paper" link: the desk opened on it (the old page for pharmacy, never linked here)
    ("    return {\"stamp\": _stamp(b), \"href\": url_for(\"bill_view\", bid=b[\"id\"])}\n",
     "    href = AR._s559_paper_href(b) if hasattr(AR, \"_s559_paper_href\") else url_for(\"bill_view\", bid=b[\"id\"])      # S559 item 4\n"
     "    return {\"stamp\": _stamp(b), \"href\": href}\n", 1),
    # AM2 (item 9) -- the cover line: a machine whose cover lives only in its old record reads it, not "No cover"
    ("    if c is None:\n        return \"No cover\", \"\"\n",
     "    if c is None:\n"
     "        ct = (_col(a, \"contract_type\") or \"\").strip()                  # S559 item 9: the old record's cover, read as it is\n"
     "        if ct and ct != \"None\":\n"
     "            prov = (_col(a, \"provider\") or \"\").strip()\n"
     "            return \"Covered (old record): %s%s\" % (ct, (\" \u2014 \" + prov) if prov else \"\"), \"\"\n"
     "        return \"No cover\", \"\"\n", 1),
    ("def totals_line(db, a, show_price):\n",
     "def _col(r, k):\n"
     "    try:\n"
     "        return r[k]\n"
     "    except (IndexError, KeyError):\n"
     "        return None\n"
     "\n\n"
     "def live_amc(db, a, today=None):\n"
     "    \"\"\"S559 item 9: True / False -- a live (not voided, not lapsed) AMC or CMC in this machine's cover history; None when\n"
     "    the history holds no cover at all (the caller then reads the old record) or cannot be read.\"\"\"\n"
     "    today = (today or _today()).isoformat()\n"
     "    try:\n"
     "        rows = db.execute(\"SELECT kind, till_day FROM asset_cover WHERE asset_id=? AND asset_created_at=? AND voided_at=''\",\n"
     "                          (a[\"id\"], a[\"created_at\"])).fetchall()\n"
     "    except sqlite3.Error:\n"
     "        return None\n"
     "    if not rows:\n"
     "        return None\n"
     "    return any(r[0] in (\"amc\", \"cmc\") and (r[1] or \"\")[:10] >= today for r in rows)\n"
     "\n\n"
     "def totals_line(db, a, show_price):\n", 1),
]

# ============================================================================================ scanner_widget.js (item 10)
SW_EDITS = [
    # SW1 -- Save while a page is being adjusted applies the adjustment first, saves once, and always closes the stage
    ("    if (inlineStamp && mode === \"doc\") { enqueue(pages.slice()); pages = []; retakeIdx = -1; if (cvScanOn) clearSrc(); renderPages(); updateSaveBar(); return; }   // S441; S523\n",
     "    if (inlineStamp && mode === \"doc\") { if (cvScanOn && adjustIdx >= 0) adjustDone();                                 // S559: the adjustment first\n"
     "      enqueue(pages.slice()); pages = []; retakeIdx = -1; if (cvScanOn) clearSrc(); stageCloseS559(); renderPages(); updateSaveBar(); return; }   // S441; S523; S559: the stage closes\n", 1),
    # SW2 -- the scan app's intake (smart outline + auto page) never makes a page from a leftover Adjust stage
    ("  function addPage(){ if (cvScanOn && adjustIdx >= 0) { adjustDone(); return; } addCaptured(warp()); }                       // S523\n",
     "  function addPage(){ if (cvScanOn && adjustIdx >= 0) { adjustDone(); return; } if (staleS559()) { stageCloseS559(); return; } addCaptured(warp()); }   // S523; S559\n", 1),
    ("  function addWhole(){ if (cvScanOn && adjustIdx >= 0) { corners = [[0,0],[ov.width,0],[ov.width,ov.height],[0,ov.height]]; adjustDone(); return; }\n",
     "  function addWhole(){ if (cvScanOn && adjustIdx >= 0) { corners = [[0,0],[ov.width,0],[ov.width,ov.height],[0,ov.height]]; adjustDone(); return; }\n"
     "    if (staleS559()) { stageCloseS559(); return; }                                                                      // S559\n", 1),
    # SW3 -- the queue's second guard, and the two helpers (inside the S441 block: only inlineStamp / the smart path use them)
    ("  var retakeIdx = -1, upq = [], upBusy = false, upSeq = 0;\n",
     "  var retakeIdx = -1, upq = [], upBusy = false, upSeq = 0;\n"
     "  // S559 (one paper, two stamps): on the intake (smart outline + auto page) the stage is only an Adjust stage; with no page under it, a leftover\n"
     "  var lastQS559 = null, adjGenS559 = 0;                                                                 // S559_FIX1 C1: the Adjust image's generation\n"
     "  function staleS559(){ return cvScanOn && autoPage && adjustIdx < 0; }\n"
     "  function stageCloseS559(){ $(\"stage\").style.display = \"none\"; $(\"addpage\").textContent = \"\\u2714 Add this page\"; adjustIdx = -1; adjustImg = null; adjGenS559++; }\n"
     "  if (inlineStamp) window.__scannerS559 = {version: \"S559.1\"};\n", 1),
    ("  function enqueue(list){\n",
     "  function enqueue(list){\n"
     "    var kS559 = list.length + \":\" + list.join(\"|\"), tS559 = Date.now();                                // S559: the same pages twice within 10 s: once\n"
     "    if (lastQS559 && lastQS559.k === kS559 && tS559 - lastQS559.t < 10000) return;\n"
     "    lastQS559 = {k: kS559, t: tS559};\n", 1),
    # SW4 (S559_FIX1 C1) -- a late-loading Adjust image never reopens the stage: adjustOpen's load step carries a generation,
    #                       bumped by stageCloseS559() (Save closes the stage) and by clearSrc(); a stale load does nothing
    ("    if (!cvReady || !pageSrc[i]) return;\n    var img = new Image();\n    img.onload = function(){\n      adjustIdx = i; adjustImg = img; retakeIdx = -1;\n",
     "    if (!cvReady || !pageSrc[i]) return;\n    var img = new Image();\n"
     "    var genS559 = ++adjGenS559;                                                                          // S559_FIX1 C1\n"
     "    img.onload = function(){\n"
     "      if (genS559 !== adjGenS559 || !pageSrc[i]) return;                                                  // S559_FIX1 C1: Saved meanwhile\n"
     "      adjustIdx = i; adjustImg = img; retakeIdx = -1;\n", 1),
    ("  function clearSrc(){ pageSrc = []; pageCorners = []; adjustIdx = -1; adjustImg = null; }\n",
     "  function clearSrc(){ pageSrc = []; pageCorners = []; adjustIdx = -1; adjustImg = null; adjGenS559++; }   // S523; S559_FIX1 C1\n", 1),
    # SW5 (S559_FIX1 C2) -- deleting an EARLIER page while a later one is adjusted keeps adjustIdx on that page; adjustDone stops
    #                       when its page is gone (never writes past the list: the same page twice in one paper)
    ("  function dropSrc(i){ pageSrc.splice(i, 1); pageCorners.splice(i, 1); if (adjustIdx === i) adjustIdx = -1; }\n",
     "  function dropSrc(i){ pageSrc.splice(i, 1); pageCorners.splice(i, 1); if (adjustIdx === i) adjustIdx = -1; else if (adjustIdx > i) adjustIdx--; }   // S523; S559_FIX1 C2\n", 1),
    ("    var i = adjustIdx; if (i < 0 || !adjustImg) { adjustIdx = -1; return; }\n",
     "    var i = adjustIdx; if (i < 0 || !adjustImg) { adjustIdx = -1; return; }\n"
     "    if (i >= pages.length) { stageCloseS559(); return; }                                                  // S559_FIX1 C2\n", 1),
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
    os.makedirs(out, exist_ok=True)
    for name, edits in (("asset_register.py", AR_EDITS), ("sorting_desk.py", SD_EDITS), ("clinic_papers.py", CP_EDITS),
                        ("asset_machine.py", AM_EDITS), ("scanner_widget.js", SW_EDITS)):
        raw = open(os.path.join(src, name), "rb").read()
        new = build(name, raw, edits)
        open(os.path.join(out, name), "wb").write(new)
        print("%s %s -> %s (%d counted edits)" % (name, FROM[name][:8], md5(new), len(edits)))


if __name__ == "__main__":
    main()
